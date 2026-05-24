from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from rules.character import Character


class WorldBase(ABC):
    world_name: str = ""
    world_id: str = ""
    world_emoji: str = ""
    tone: str = ""
    narrative_style: str = ""
    default_setting: str = ""
    gm_persona: str = ""
    check_keyword: str = "检定"
    description: str = ""

    @abstractmethod
    def get_system_prompt(self, character: Character) -> str:
        ...

    @abstractmethod
    def describe_critical_success(self, attribute: str) -> str:
        ...

    @abstractmethod
    def describe_critical_failure(self, attribute: str) -> str:
        ...

    @abstractmethod
    def describe_check_success(self, attribute: str, total: int, dc: int) -> str:
        ...

    @abstractmethod
    def describe_check_failure(self, attribute: str, total: int, dc: int) -> str:
        ...

    @abstractmethod
    def on_critical_success(self, character: Character) -> str:
        ...

    @abstractmethod
    def on_critical_failure(self, character: Character) -> str:
        ...

    def format_check_request(self, attribute: str, dc: int) -> str:
        return f"[{self.check_keyword}:{attribute} DC={dc}]"

    def format_exp_reward(self, amount: int) -> str:
        return f"[经验:{amount}]"
