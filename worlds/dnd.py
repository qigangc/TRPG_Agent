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
【判定请求】当需要判定玩家行动结果时，输出格式：[检定:属性名 DC=数值]，属性名可选：力量、敏捷、体质、智力、感知、魅力
【经验奖励】当玩家完成重要任务、击败强敌或精彩扮演时，在回复末尾输出：[经验:数值]
【激励骰】当玩家做出特别精彩的扮演时，可以给予激励骰，输出：[激励骰:1]，激励骰可在下次检定时额外加1d6
【当前角色】
{character.summary()}
【规则提醒】
- 大成功(自然20)必定成功，描述为命运的眷顾
- 大失败(自然1)必定失败，描述为厄运降临
- DC参考：简单10，中等15，困难20，极难25
- 一次回复中最多请求一个判定，等待判定结果后再继续叙事
- 保持叙事连贯，根据角色属性和判定结果推动剧情
【快捷指令】每次回复末尾，根据当前场景提供3~4个建议行动，格式：[快捷:行动描述]，例如：
[快捷:搜查房间里的橡木书桌]
[快捷:试图用威吓让酒馆老板开口]
[快捷:拔出长剑，拉开距离]
[快捷:仔细聆听门后的动静]"""

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
