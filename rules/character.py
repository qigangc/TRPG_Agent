from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from config import Config

ATTRIBUTE_NAMES = [
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
]

ATTRIBUTE_LABELS = {
    "strength": "力量",
    "dexterity": "敏捷",
    "constitution": "体质",
    "intelligence": "智力",
    "wisdom": "感知",
    "charisma": "魅力",
}


def modifier(score: int) -> int:
    """Calculate attribute modifier from score: (score - 10) // 2."""
    return (score - 10) // 2


@dataclass
class Character:
    name: str = ""
    level: int = 1
    exp: int = 0

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    attribute_points: int = Config.INITIAL_ATTRIBUTE_POINTS

    background: str = ""
    inventory: List[str] = field(default_factory=list)
    inspiration: int = 0
    breakthrough_count: int = 0

    current_scene: str = ""

    @property
    def max_hp(self) -> int:
        return 10 + modifier(self.constitution) * self.level

    @property
    def hp(self) -> int:
        return self.max_hp

    def get_attribute(self, attr_name: str) -> int:
        return getattr(self, attr_name, 10)

    def set_attribute(self, attr_name: str, value: int) -> bool:
        if attr_name not in ATTRIBUTE_NAMES:
            return False
        if value < 1 or value > 20:
            return False
        old = getattr(self, attr_name)
        diff = value - old
        if diff > self.attribute_points:
            return False
        self.attribute_points -= diff
        setattr(self, attr_name, value)
        return True

    def get_modifier(self, attr_name: str) -> int:
        return modifier(self.get_attribute(attr_name))

    def exp_to_next_level(self) -> int:
        return self.level * Config.EXP_THRESHOLD

    def gain_exp(self, amount: int) -> bool:
        """Add experience. Returns True if leveled up."""
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_to_next_level():
            self.exp -= self.exp_to_next_level()
            self.level += 1
            self.attribute_points += 1
            leveled = True
        return leveled

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level,
            "exp": self.exp,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
            "attribute_points": self.attribute_points,
            "background": self.background,
            "inventory": self.inventory,
            "inspiration": self.inspiration,
            "breakthrough_count": self.breakthrough_count,
            "current_scene": self.current_scene,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Character:
        c = cls()
        for key, value in data.items():
            if hasattr(c, key):
                setattr(c, key, value)
        return c

    def summary(self) -> str:
        lines = [
            f"【{self.name}】等级 {self.level}",
            f"经验: {self.exp}/{self.exp_to_next_level()}",
        ]
        for attr in ATTRIBUTE_NAMES:
            val = self.get_attribute(attr)
            mod = self.get_modifier(attr)
            sign = "+" if mod >= 0 else ""
            lines.append(f"  {ATTRIBUTE_LABELS[attr]}: {val} ({sign}{mod})")
        lines.append(f"HP: {self.hp}")
        lines.append(f"可用属性点: {self.attribute_points}")
        if self.inspiration > 0:
            lines.append(f"激励骰: {self.inspiration}")
        if self.breakthrough_count > 0:
            lines.append(f"突破进度: {self.breakthrough_count}/3")
        if self.inventory:
            lines.append(f"物品: {', '.join(self.inventory)}")
        return "\n".join(lines)
