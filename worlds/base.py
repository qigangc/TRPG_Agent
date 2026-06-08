from __future__ import annotations

from abc import ABC, abstractmethod

from rules.character import Character


class WorldBase(ABC):
    world_name: str = ""
    world_id: str = ""
    world_emoji: str = ""
    tone: str = ""
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
