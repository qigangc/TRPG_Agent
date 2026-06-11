from __future__ import annotations

from rules.character import Character, ATTRIBUTE_LABELS
from worlds.base import WorldBase


class DNDWorld(WorldBase):
    world_name = "龙与地下城"
    world_id = "dnd"
    world_emoji = "⚔️"
    tone = "史诗、正式、庄重"
    check_keyword = "检定"
    description = "剑与魔法的史诗大陆，古老地下城与巨龙守护着无尽宝藏。适合喜欢经典奇幻冒险的玩家。"

    def get_system_prompt(self, character: Character) -> str:
        return f"""你是一位经验丰富的地下城主(DM)，正在主持一场龙与地下城风格的冒险。
【语气风格】史诗、正式、庄重，带有中世纪奇幻色彩
【叙事方式】详细描写场景氛围，注重沉浸感，使用"你看到..."、"你感受到..."等第二人称叙事
【当前角色】
{character.summary()}
【规则提醒】
- 大成功(自然20)必定成功，描述为命运的眷顾
- 大失败(自然1)必定失败，描述为厄运降临
- DC参考：简单10，中等15，困难20，极难25
- 一次回复中最多请求一个判定，等待判定结果后再继续叙事
- 保持叙事连贯，根据角色属性和判定结果推动剧情
【输出格式】
你的每次回复将被解析为结构化 JSON，包含以下字段：
- narrative: 叙事文本，你的主要回复内容
- check: 检定请求，格式为 {{"attribute": "属性英文名", "dc": 数值}}，属性可选 strength/dexterity/constitution/intelligence/wisdom/charisma
- exp_reward: 经验奖励数值，当玩家完成重要任务、击败强敌或精彩扮演时设置
- inspiration: 激励骰数量，当玩家做出特别精彩的扮演时给予 1，可在下次检定时额外加1d6
- breakthrough: 突破属性名，当角色触发突破条件时填写属性中文名（如"力量"），仅在CNC世界观使用
- quick_actions: 建议行动列表，根据当前场景提供3~4个字符串
- scene: 当前场景描述，用于更新场景画面"""

    def describe_critical_success(self, attribute: str) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"命运的眷顾！{attr_cn}检定大成功！诸神今日与你同在！"

    def describe_critical_failure(self, attribute: str) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"厄运降临！{attr_cn}检定大失败！命运在此刻与你为敌..."

    def describe_check_success(self, attribute: str, total: int, dc: int) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"{attr_cn}检定成功！{total} ≥ {dc}，你的努力得到了回报。"

    def describe_check_failure(self, attribute: str, total: int, dc: int) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"{attr_cn}检定失败...{total} < {dc}，这次运气不在你这边。"

    def on_critical_success(self, character: Character) -> str:
        return ""

    def on_critical_failure(self, character: Character) -> str:
        return ""
