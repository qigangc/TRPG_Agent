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

ATTRIBUTE_ICONS = {
    "strength": "💪",
    "dexterity": "🏃",
    "constitution": "❤️",
    "intelligence": "🧠",
    "wisdom": "👁️",
    "charisma": "✨",
}

PRESET_CHARACTERS = {
    "warrior": {
        "name": "艾尔德里克",
        "label": "⚔️ 战士",
        "description": "身经百战的战士，力量与体质出众，适合正面冲锋。",
        "strength": 16,
        "dexterity": 12,
        "constitution": 15,
        "intelligence": 8,
        "wisdom": 10,
        "charisma": 9,
        "background": "出身于边境卫队的老兵，在无数战斗中磨砺出钢铁般的意志。退役后踏上了寻找失落王冠的旅途。",
    },
    "rogue": {
        "name": "暗影·薇拉",
        "label": "🗡️ 盗贼",
        "description": "敏捷如风的盗贼，擅长潜行与巧手，适合灵活周旋。",
        "strength": 8,
        "dexterity": 17,
        "constitution": 10,
        "intelligence": 13,
        "wisdom": 12,
        "charisma": 10,
        "background": "贫民窟长大的孤儿，靠一双巧手和敏捷的身法在城市中生存。最近接到了一个改变命运的任务。",
    },
    "mage": {
        "name": "塞拉斯",
        "label": "🔮 法师",
        "description": "博学多识的法师，智力与感知超群，适合用知识解决问题。",
        "strength": 6,
        "dexterity": 10,
        "constitution": 9,
        "intelligence": 17,
        "wisdom": 14,
        "charisma": 8,
        "background": "魔法学院的天才毕业生，在禁忌典籍中发现了一个被封印的秘密，被迫踏上了逃亡之路。",
    },
    "bard": {
        "name": "莉莉安",
        "label": "🎵 吟游诗人",
        "description": "魅力四射的吟游诗人，擅长社交与鼓舞，适合嘴遁流。",
        "strength": 8,
        "dexterity": 13,
        "constitution": 10,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 17,
        "background": "走遍大陆的吟游诗人，用歌声和故事记录着每一个冒险。她相信每一首歌都藏着一个真实的秘密。",
    },
    "monk": {
        "name": "无尘",
        "label": "🥋 武僧",
        "description": "内外兼修的武僧，感知与敏捷均衡，适合中庸稳健。",
        "strength": 12,
        "dexterity": 15,
        "constitution": 12,
        "intelligence": 10,
        "wisdom": 15,
        "charisma": 6,
        "background": "山中寺庙的修行者，在冥想中看到了世界的裂痕，决定下山查明真相。以拳为剑，以心为盾。",
    },
}


def modifier(score: int) -> int:
    """Calculate attribute modifier from score: (score - 10) // 2."""
    return (score - 10) // 2


def _modifier_bar(score: int) -> str:
    mod = modifier(score)
    filled = max(0, min(10, mod + 5))
    bar = "█" * filled + "░" * (10 - filled)
    sign = "+" if mod >= 0 else ""
    return f"{bar} {sign}{mod}"


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
    sanity: int = 0
    madness_count: int = 0

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
            "sanity": self.sanity,
            "madness_count": self.madness_count,
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

    def card_html(self, world_id: str = "dnd") -> str:
        exp_pct = int(self.exp / self.exp_to_next_level() * 100) if self.exp_to_next_level() > 0 else 0

        attr_rows = ""
        for attr in ATTRIBUTE_NAMES:
            val = self.get_attribute(attr)
            mod = self.get_modifier(attr)
            sign = "+" if mod >= 0 else ""
            bar = _modifier_bar(val)
            icon = ATTRIBUTE_ICONS.get(attr, "")
            label = ATTRIBUTE_LABELS[attr]
            attr_rows += f"""
            <tr>
                <td style="padding:4px 8px;">{icon} {label}</td>
                <td style="padding:4px 8px;text-align:center;font-weight:bold;">{val}</td>
                <td style="padding:4px 8px;font-family:monospace;font-size:12px;">{bar}</td>
                <td style="padding:4px 8px;text-align:center;color:{'#2ecc71' if mod >= 0 else '#e74c3c'};">{sign}{mod}</td>
            </tr>"""

        extras = ""
        if self.inspiration > 0:
            extras += f'<div style="margin:4px 0;">🎲 激励骰: <b>{self.inspiration}</b></div>'
        if self.breakthrough_count > 0:
            extras += f'<div style="margin:4px 0;">🌟 突破进度: <b>{self.breakthrough_count}/3</b></div>'
        if self.sanity != 0:
            color = "#2ecc71" if self.sanity > 0 else "#e74c3c"
            extras += f'<div style="margin:4px 0;color:{color};">🧠 理智: <b>{self.sanity}</b></div>'
        if self.madness_count > 0:
            extras += f'<div style="margin:4px 0;color:#e74c3c;">🌀 疯狂进度: <b>{self.madness_count}/3</b></div>'
        if self.attribute_points > 0:
            extras += f'<div style="margin:4px 0;color:#f39c12;">⬆ 可分配属性点: <b>{self.attribute_points}</b></div>'

        inventory_html = ""
        if self.inventory:
            items = "".join(f'<span style="background:#34495e;padding:2px 8px;border-radius:10px;margin:2px;display:inline-block;font-size:12px;">{item}</span>' for item in self.inventory)
            inventory_html = f'<div style="margin-top:8px;">🎒 <b>物品栏</b><div style="margin-top:4px;">{items}</div></div>'

        bg_html = ""
        if self.background:
            bg_html = f'<div style="margin-top:8px;padding:8px;background:#1a1a2e;border-radius:6px;font-size:12px;color:#bdc3c7;">📜 {self.background}</div>'

        return f"""
        <div style="font-family:'Segoe UI',sans-serif;color:#ecf0f1;max-width:100%;">
            <div style="text-align:center;margin-bottom:12px;">
                <div style="font-size:24px;font-weight:bold;">🛡️ {self.name}</div>
                <div style="font-size:14px;color:#95a5a6;">Lv.{self.level} 冒险者</div>
            </div>
            <div style="background:#2c3e50;border-radius:8px;padding:12px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span>❤️ HP</span><span><b>{self.hp}</b></span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span>⭐ 经验</span><span>{self.exp}/{self.exp_to_next_level()}</span>
                </div>
                <div style="background:#1a1a2e;border-radius:4px;height:8px;overflow:hidden;">
                    <div style="background:linear-gradient(90deg,#f39c12,#e67e22);height:100%;width:{exp_pct}%;"></div>
                </div>
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <tr style="border-bottom:1px solid #34495e;">
                    <th style="padding:4px 8px;text-align:left;">属性</th>
                    <th style="padding:4px 8px;text-align:center;">数值</th>
                    <th style="padding:4px 8px;text-align:left;">修正</th>
                    <th style="padding:4px 8px;text-align:center;">±</th>
                </tr>
                {attr_rows}
            </table>
            {extras}
            {inventory_html}
            {bg_html}
        </div>
        """
