from __future__ import annotations

from rules.character import Character, ATTRIBUTE_LABELS
from worlds.base import WorldBase


class CNCWorld(WorldBase):
    world_name = "国产奇幻"
    world_id = "cnc"
    world_emoji = "🐉"
    tone = "搞笑、轻快、接地气"
    narrative_style = "沙雕魔幻，适度打破第四面墙，吐槽玩家选择"
    default_setting = "现代中国奇幻世界，修仙穿越混合体，外卖小哥也能修仙，地铁上可能遇到妖精。"
    gm_persona = "你是一位风格独特的游戏主持人，喜欢吐槽玩家的选择，偶尔打破第四面墙，但绝不亏待有趣的操作。"
    check_keyword = "挑战"
    description = "现代修仙穿越沙雕世界，外卖小哥也能修仙，地铁上可能遇到妖精。适合喜欢轻松搞笑的玩家。"

    def get_system_prompt(self, character: Character) -> str:
        return f"""你是一位风格独特的游戏主持人，正在主持一场国产沙雕奇幻冒险。
【语气风格】搞笑、轻快、接地气，可以使用网络梗和流行语
【叙事方式】轻松幽默，适度打破第四面墙，吐槽玩家选择，但不要恶意嘲讽
【判定请求】当需要判定玩家行动结果时，输出格式：[挑战:属性名 DC=数值]，属性名可选：力量、敏捷、体质、智力、感知、魅力
【经验奖励】当玩家搞出骚操作或推进剧情时，在回复末尾输出：[经验:数值]
【翻车事件】大失败(自然1)时，除了判定失败，还要额外添加一个搞笑的倒霉后果
【修仙突破】当累计3次大成功时触发"修仙突破"，角色可以+2任意属性（不消耗属性点），由你决定加在哪个属性上并输出：[突破:属性名]
【当前角色】
{character.summary()}
【规则提醒】
- 大成功(自然20)要夸张庆祝，还可以让玩家获得额外行动机会
- 大失败(自然1)要戏剧性翻车，加上搞笑倒霉后果
- DC参考：简单10，中等15，困难20，极难25
- 一次回复中最多请求一个判定，等待判定结果后再继续叙事
- 保持叙事连贯，根据角色属性和判定结果推动剧情
- 可以用现代网络用语，比如"这波操作""绝绝子""666"等
【快捷指令】每次回复末尾，根据当前场景提供3~4个建议行动，格式：[快捷:行动描述]，例如：
[快捷:翻窗潜入看看里面有啥好东西]
[快捷:用方言套近乎打探消息]
[快捷:直接开大，莽上去]
[快捷:掏出手机查查这地方有没有攻略]"""

    def describe_critical_success(self, attribute: str) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"🎉 自然20！{attr_cn}挑战大成功！这波天秀！"

    def describe_critical_failure(self, attribute: str) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"💥 自然1！{attr_cn}挑战大失败！翻车了翻车了！"

    def describe_check_success(self, attribute: str, total: int, dc: int) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"{attr_cn}挑战成功！{total} ≥ {dc}，稳了！"

    def describe_check_failure(self, attribute: str, total: int, dc: int) -> str:
        attr_cn = ATTRIBUTE_LABELS.get(attribute, attribute)
        return f"{attr_cn}挑战失败...{total} < {dc}，寄了..."

    def on_critical_success(self, character: Character) -> str:
        character.breakthrough_count += 1
        if character.breakthrough_count >= 3:
            character.breakthrough_count = 0
            return "breakthrough"
        return f"大成功！突破进度: {character.breakthrough_count}/3"

    def on_critical_failure(self, character: Character) -> str:
        return "翻车事件触发！GM会为你安排一个额外的倒霉后果..."
