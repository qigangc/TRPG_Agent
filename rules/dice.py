import random
from dataclasses import dataclass


@dataclass
class RollResult:
    value: int
    is_critical_success: bool
    is_critical_failure: bool


def roll_d20() -> RollResult:
    """Roll a d20 die and return structured result with critical flags."""
    value = random.randint(1, 20)
    return RollResult(
        value=value,
        is_critical_success=(value == 20),
        is_critical_failure=(value == 1),
    )


def roll_with_advantage() -> RollResult:
    """Roll d20 twice and take the higher result."""
    r1 = roll_d20()
    r2 = roll_d20()
    chosen = r1 if r1.value >= r2.value else r2
    return chosen


def roll_with_disadvantage() -> RollResult:
    """Roll d20 twice and take the lower result."""
    r1 = roll_d20()
    r2 = roll_d20()
    chosen = r1 if r1.value <= r2.value else r2
    return chosen


def roll_inspiration() -> int:
    """Roll a d6 inspiration die (DND specific)."""
    return random.randint(1, 6)
