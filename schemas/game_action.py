from typing import List, Optional

from pydantic import BaseModel, Field


class CheckRequest(BaseModel):
    attribute: str = Field(description="属性英文名: strength/dexterity/constitution/intelligence/wisdom/charisma")
    dc: int = Field(description="难度等级，通常 10-25")


class GameAction(BaseModel):
    narrative: str = Field(description="DM 叙事文本，不含任何标签或元数据")
    check: Optional[CheckRequest] = Field(default=None)
    exp_reward: Optional[int] = Field(default=None)
    inspiration: Optional[int] = Field(default=None)
    breakthrough: Optional[str] = Field(default=None)
    quick_actions: List[str] = Field(default_factory=list)
    scene: Optional[str] = Field(default=None)
