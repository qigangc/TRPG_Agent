from __future__ import annotations

import logging
import random
from typing import Dict, Generator, List, Optional, Tuple

from config import Config
from llm_client import LLMClient
from rules.character import Character
from rules.events import make_check, make_check_with_roll, CheckResult, ATTRIBUTE_CN
from storage import save_game, load_game, list_saves
from worlds import get_world, WORLD_REGISTRY
from worlds.base import WorldBase

logger = logging.getLogger(__name__)


class GameEngine:
    def __init__(self):
        self.character: Optional[Character] = None
        self.world_id: str = "dnd"
        self.world: WorldBase = get_world("dnd")
        self.messages: List[Dict[str, str]] = []
        self.last_quick_actions: List[str] = []
        self.llm: Optional[LLMClient] = None
        self._initialized = False
        self.pending_check: Optional[Dict] = None
        self._pending_exp: Optional[Tuple[int, bool]] = None

    def _ensure_llm(self) -> LLMClient:
        if self.llm is None:
            self.llm = LLMClient()
        return self.llm

    def set_pending_check(self, attribute: str, dc: int) -> None:
        """记录待处理的检定请求，等待前端骰子结果。"""
        modifier_value = self.character.get_modifier(attribute) if self.has_character else 0
        self.pending_check = {
            "attribute": attribute,
            "dc": dc,
            "attribute_label": ATTRIBUTE_CN.get(attribute, attribute),
            "modifier": modifier_value,
        }

    def resolve_check(
        self,
        roll_value: int,
        use_inspiration: bool = False,
        inspiration_roll: int = 0,
    ) -> Tuple[CheckResult, str]:
        """
        使用前端传来的骰子结果执行检定。
        调用 make_check_with_roll()，处理世界特效，返回 (CheckResult, narrative_desc)。
        """
        if not self.has_character:
            raise ValueError("No character to perform check")
        if self.pending_check is None:
            raise ValueError("No pending check to resolve")

        attr = self.pending_check["attribute"]
        dc = self.pending_check["dc"]

        result = make_check_with_roll(
            self.character, attr, dc,
            roll_value=roll_value,
            use_inspiration=use_inspiration,
            inspiration_roll=inspiration_roll,
        )

        if result.is_critical_success:
            desc = self.world.describe_critical_success(attr)
            effect = self.world.on_critical_success(self.character)
            if effect == "breakthrough":
                desc += "\n🌟 修仙突破触发！即将获得属性提升！"
            elif effect:
                desc += f"\n{effect}"
        elif result.is_critical_failure:
            desc = self.world.describe_critical_failure(attr)
            effect = self.world.on_critical_failure(self.character)
            if effect:
                desc += f"\n{effect}"
        elif result.success:
            desc = self.world.describe_check_success(attr, result.total, dc)
        else:
            desc = self.world.describe_check_failure(attr, result.total, dc)

        full_desc = f"{result.description}\n{desc}"
        return result, full_desc

    def hidden_exp_gain(self) -> Optional[Tuple[int, bool]]:
        """
        隐藏经验获取：每次交互 30% 概率获得 5-25 经验。
        返回 (amount, leveled) 或 None。
        """
        if not self.has_character:
            return None
        if random.random() < 0.3:
            amount = random.randint(5, 25)
            leveled = self.character.gain_exp(amount)
            logger.info(f"Hidden exp gained: {amount}, leveled up: {leveled}")
            return (amount, leveled)
        return None

    @property
    def has_character(self) -> bool:
        return self.character is not None and self.character.name != ""

    def create_character(
        self,
        name: str,
        strength: int = 10,
        dexterity: int = 10,
        constitution: int = 10,
        intelligence: int = 10,
        wisdom: int = 10,
        charisma: int = 10,
        background: str = "",
    ) -> Character:
        """Create a new character with given attributes."""
        c = Character(name=name, background=background)
        c.attribute_points = 0
        c.strength = strength
        c.dexterity = dexterity
        c.constitution = constitution
        c.intelligence = intelligence
        c.wisdom = wisdom
        c.charisma = charisma

        self.character = c
        self.messages = []
        self.last_quick_actions = []
        self._initialized = False
        self.pending_check = None
        self._pending_exp = None
        return c

    def switch_world(self, world_id: str) -> str:
        """Switch world, keep character, clear conversation."""
        if world_id not in WORLD_REGISTRY:
            return f"Unknown world: {world_id}"

        self.world_id = world_id
        self.world = get_world(world_id)
        self.messages = []
        self.last_quick_actions = []
        self._initialized = False
        self.pending_check = None
        self._pending_exp = None
        return f"Switched to {self.world.world_name}"

    def _build_system_prompt(self) -> str:
        if not self.has_character:
            return self.world.get_system_prompt(Character())
        return self.world.get_system_prompt(self.character)

    def _trim_messages(self) -> None:
        max_rounds = Config.MAX_HISTORY
        if len(self.messages) > max_rounds * 2:
            self.messages = self.messages[-(max_rounds * 2):]

    def _init_game(self) -> None:
        if self._initialized:
            return
        self._initialized = True

    def _restore_quick_actions(self) -> None:
        self.last_quick_actions = []
        for msg in self.messages:
            if msg.get("role") != "assistant":
                continue
            actions = LLMClient.parse_quick_actions(msg.get("content", ""))
            if actions:
                self.last_quick_actions = actions

    def process_input(self, user_input: str) -> Generator[str, None, None]:
        """
        Process user input and yield response chunks.
        Handles check requests, exp rewards, inspiration, breakthroughs.
        """
        if not self.has_character:
            yield "⚠️ Please create a character first!"
            return

        self._init_game()

        self.messages.append({"role": "user", "content": user_input})
        self._trim_messages()

        llm = self._ensure_llm()
        system_prompt = self._build_system_prompt()

        full_response = ""
        try:
            for chunk in llm.chat_stream(system_prompt, self.messages):
                full_response += chunk
                yield chunk
        except RuntimeError as e:
            error_msg = f"\n\n⚠️ AI service error: {e}"
            yield error_msg
            full_response += error_msg

        self.messages.append({"role": "assistant", "content": full_response})
        self._process_ai_output(full_response)
        self._pending_exp = self.hidden_exp_gain()

    def _update_scene(self, text: str) -> None:
        """Extract scene description from AI output and update character.current_scene."""
        import re
        scene_match = re.search(r"【场景[：:]\s*(.+?)】", text)
        if not scene_match:
            scene_match = re.search(r"\[场景[：:]\s*(.+?)\]", text)
        if scene_match:
            self.character.current_scene = scene_match.group(1).strip()

    def _process_ai_output(self, text: str) -> None:
        """Process tagged commands in AI output (exp, inspiration, breakthrough, scene)."""
        if not self.has_character:
            return

        llm = self._ensure_llm()
        self._update_scene(text)

        for amount in llm.parse_exp_rewards(text):
            leveled = self.character.gain_exp(amount)
            logger.info(f"Character gained {amount} exp. Leveled up: {leveled}")

        for amount in llm.parse_inspiration(text):
            self.character.inspiration += amount
            logger.info(f"Character gained {amount} inspiration dice")

        for attr in llm.parse_breakthrough(text):
            if hasattr(self.character, attr):
                current = getattr(self.character, attr)
                setattr(self.character, attr, current + 2)
                logger.info(f"Breakthrough! {attr} +2")

    def perform_check(
        self,
        attribute: str,
        dc: int,
        advantage: bool = False,
        disadvantage: bool = False,
        use_inspiration: bool = False,
    ) -> Tuple[CheckResult, str]:
        """
        Execute a check and return (result, narrative_description).
        Also handles world-specific critical effects.
        """
        if not self.has_character:
            raise ValueError("No character to perform check")

        result = make_check(
            self.character, attribute, dc,
            advantage=advantage,
            disadvantage=disadvantage,
            use_inspiration=use_inspiration,
        )

        if result.is_critical_success:
            desc = self.world.describe_critical_success(attribute)
            effect = self.world.on_critical_success(self.character)
            if effect == "breakthrough":
                desc += "\n🌟 修仙突破触发！即将获得属性提升！"
            elif effect:
                desc += f"\n{effect}"
        elif result.is_critical_failure:
            desc = self.world.describe_critical_failure(attribute)
            effect = self.world.on_critical_failure(self.character)
            if effect:
                desc += f"\n{effect}"
        elif result.success:
            desc = self.world.describe_check_success(attribute, result.total, dc)
        else:
            desc = self.world.describe_check_failure(attribute, result.total, dc)

        full_desc = f"{result.description}\n{desc}"
        return result, full_desc

    def save(self) -> str:
        """Save current game. Returns file path."""
        if not self.has_character:
            raise ValueError("No character to save")
        return save_game(self.character, self.world_id, self.messages)

    def load(self, filepath: str) -> str:
        """Load game from file. Returns status message."""
        data = load_game(filepath)
        self.character = data["character"]
        self.world_id = data["world_id"]
        self.world = get_world(self.world_id)
        self.messages = data.get("messages", [])
        self._restore_quick_actions()
        self._initialized = True
        self.pending_check = None
        self._pending_exp = None
        return f"Loaded: {self.character.name} (Lv.{self.character.level}) in {self.world.world_name}"

    def get_save_list(self) -> List[Dict]:
        return list_saves()

    def get_character_info(self) -> str:
        if not self.has_character:
            return "No character created"
        return self.character.summary()

    def get_world_info(self) -> str:
        return f"Current world: {self.world.world_name} ({self.world.tone})"
