from __future__ import annotations

import logging
import re
import time
from typing import Dict, Generator, List, Optional

from zhipuai import ZhipuAI

from config import Config

logger = logging.getLogger(__name__)

PATTERN_CHECK = re.compile(r"\[(?:检定|挑战):(\w+)\s+DC=(\d+)\]")
PATTERN_EXP = re.compile(r"\[经验:(\d+)\]")
PATTERN_INSPIRATION = re.compile(r"\[激励骰:(\d+)\]")
PATTERN_BREAKTHROUGH = re.compile(r"\[突破:(\w+)\]")


class LLMClient:
    def __init__(self):
        if not Config.ZHIPU_API_KEY:
            raise ValueError("ZHIPU_API_KEY is not set. Please configure .env file.")
        self.client = ZhipuAI(api_key=Config.ZHIPU_API_KEY)
        self.model = Config.MODEL_NAME

    def chat_stream(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> Generator[str, None, None]:
        """
        Stream chat completion with retry logic.
        Yields text chunks as they arrive.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        for attempt in range(Config.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=Config.TEMPERATURE,
                    max_tokens=Config.MAX_TOKENS,
                    stream=True,
                )

                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content

                return

            except Exception as e:
                logger.warning(f"LLM request attempt {attempt + 1} failed: {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    time.sleep(wait)
                else:
                    raise RuntimeError(
                        f"LLM request failed after {Config.MAX_RETRIES} retries: {e}"
                    )

    def chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """Non-streaming chat completion. Returns full response text."""
        full_text = ""
        for chunk in self.chat_stream(system_prompt, messages):
            full_text += chunk
        return full_text

    @staticmethod
    def parse_check_requests(text: str) -> List[Dict[str, any]]:
        """Parse check requests from AI output, e.g. [检定:力量 DC=15] or [挑战:敏捷 DC=20]."""
        results = []
        for match in PATTERN_CHECK.finditer(text):
            attr_cn = match.group(1)
            dc = int(match.group(2))
            attr_en = _cn_attr_to_en(attr_cn)
            results.append({
                "attribute": attr_en,
                "attribute_cn": attr_cn,
                "dc": dc,
                "raw": match.group(0),
            })
        return results

    @staticmethod
    def parse_exp_rewards(text: str) -> List[int]:
        """Parse experience rewards from AI output, e.g. [经验:50]."""
        return [int(m.group(1)) for m in PATTERN_EXP.finditer(text)]

    @staticmethod
    def parse_inspiration(text: str) -> List[int]:
        """Parse inspiration dice rewards from AI output, e.g. [激励骰:1]."""
        return [int(m.group(1)) for m in PATTERN_INSPIRATION.finditer(text)]

    @staticmethod
    def parse_breakthrough(text: str) -> List[str]:
        """Parse breakthrough rewards from AI output, e.g. [突破:力量]."""
        results = []
        for m in PATTERN_BREAKTHROUGH.finditer(text):
            attr_cn = m.group(1)
            attr_en = _cn_attr_to_en(attr_cn)
            results.append(attr_en)
        return results

    @staticmethod
    def strip_tags(text: str) -> str:
        """Remove all tagged commands from display text."""
        cleaned = PATTERN_CHECK.sub("", text)
        cleaned = PATTERN_EXP.sub("", cleaned)
        cleaned = PATTERN_INSPIRATION.sub("", cleaned)
        cleaned = PATTERN_BREAKTHROUGH.sub("", cleaned)
        return cleaned.strip()


_ATTR_MAP_CN_TO_EN = {
    "力量": "strength",
    "敏捷": "dexterity",
    "体质": "constitution",
    "智力": "intelligence",
    "感知": "wisdom",
    "魅力": "charisma",
}


def _cn_attr_to_en(cn: str) -> str:
    return _ATTR_MAP_CN_TO_EN.get(cn, cn.lower())
