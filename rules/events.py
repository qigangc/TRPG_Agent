from __future__ import annotations

from dataclasses import dataclass

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


def make_check_with_roll(
    character: Character,
    attribute: str,
    dc: int,
    roll_value: int,
    use_inspiration: bool = False,
    inspiration_roll: int = 0,
) -> CheckResult:
    """
    Perform a d20 attribute check with a user-supplied roll value.
    Used when the user rolls dice in the frontend.
    """
    return _compute_check(character, attribute, dc, roll_value, use_inspiration, inspiration_roll)


def _compute_check(
    character: Character,
    attribute: str,
    dc: int,
    roll_value: int,
    use_inspiration: bool = False,
    inspiration_roll: int = 0,
) -> CheckResult:
    mod = character.get_modifier(attribute)
    total = roll_value + mod

    if use_inspiration and character.inspiration > 0:
        if inspiration_roll <= 0:
            from rules.dice import roll_inspiration
            inspiration_roll = roll_inspiration()
        total += inspiration_roll
        character.inspiration -= 1

    is_crit_success = roll_value == 20
    is_crit_failure = roll_value == 1

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
        desc = f"[d20] {attr_cn} Check Success: {roll_value}+{mod}={total} >= {dc}({dc_label})"
    else:
        desc = f"[d20] {attr_cn} Check Failure: {roll_value}+{mod}={total} < {dc}({dc_label})"

    return CheckResult(
        success=success,
        roll_value=roll_value,
        modifier_value=mod,
        total=total,
        dc=dc,
        is_critical_success=is_crit_success,
        is_critical_failure=is_crit_failure,
        attribute=attribute,
        description=desc,
    )
