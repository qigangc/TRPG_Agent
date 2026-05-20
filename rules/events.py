from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from rules.dice import roll_d20, roll_with_advantage, roll_with_disadvantage
from rules.character import Character

ATTRIBUTE_CN = {
    "strength": "力量",
    "dexterity": "敏捷",
    "constitution": "体质",
    "intelligence": "智力",
    "wisdom": "感知",
    "charisma": "魅力",
}

DC_LABELS = {
    10: "简单",
    15: "中等",
    20: "困难",
    25: "极难",
}


@dataclass
class CheckResult:
    success: bool
    roll_value: int
    modifier_value: int
    total: int
    dc: int
    is_critical_success: bool
    is_critical_failure: bool
    attribute: str
    description: str


def make_check(
    character: Character,
    attribute: str,
    dc: int,
    advantage: bool = False,
    disadvantage: bool = False,
    use_inspiration: bool = False,
) -> CheckResult:
    """
    Perform a d20 attribute check.

    - Roll d20 (+ advantage/disadvantage)
    - Add attribute modifier
    - Compare vs DC
    - Natural 20 = critical success, natural 1 = critical failure
    """
    if advantage and disadvantage:
        advantage = False
        disadvantage = False

    if advantage:
        roll = roll_with_advantage()
    elif disadvantage:
        roll = roll_with_disadvantage()
    else:
        roll = roll_d20()

    mod = character.get_modifier(attribute)
    total = roll.value + mod

    if use_inspiration and character.inspiration > 0:
        from rules.dice import roll_inspiration
        insp = roll_inspiration()
        total += insp
        character.inspiration -= 1

    is_crit_success = roll.is_critical_success
    is_crit_failure = roll.is_critical_failure

    if is_crit_success:
        success = True
    elif is_crit_failure:
        success = False
    else:
        success = total >= dc

    attr_cn = ATTRIBUTE_CN.get(attribute, attribute)
    dc_label = DC_LABELS.get(dc, str(dc))

    if is_crit_success:
        desc = f"[d20] Natural 20! {attr_cn} Critical Success! (DC{dc} {dc_label})"
    elif is_crit_failure:
        desc = f"[d20] Natural 1! {attr_cn} Critical Failure! (DC{dc} {dc_label})"
    elif success:
        desc = f"[d20] {attr_cn} Check Success: {roll.value}+{mod}={total} >= {dc}({dc_label})"
    else:
        desc = f"[d20] {attr_cn} Check Failure: {roll.value}+{mod}={total} < {dc}({dc_label})"

    return CheckResult(
        success=success,
        roll_value=roll.value,
        modifier_value=mod,
        total=total,
        dc=dc,
        is_critical_success=is_crit_success,
        is_critical_failure=is_crit_failure,
        attribute=attribute,
        description=desc,
    )
