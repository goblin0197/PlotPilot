"""战斗编排 Skill — 为战斗场景提供招式/节奏编排的增强

适用于武侠、玄幻、仙侠、奇幻等包含战斗场景的题材。
"""

from typing import List
from application.engine.theme.theme_agent import ThemeSkill


class BattleChoreographySkill(ThemeSkill):
    """战斗编排器 — 增强战斗场景的动作描写质量"""

    @property
    def skill_key(self) -> str:
        """读取或计算 `skill_key` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_key` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "battle_choreography"

    @property
    def skill_name(self) -> str:
        """读取或计算 `skill_name` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_name` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "战斗编排"

    @property
    def skill_description(self) -> str:
        """读取或计算 `skill_description` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_description` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "增强战斗场景的招式拆解、节奏控制和画面感，避免「他一拳打去」式的空泛描写"

    @property
    def compatible_genres(self) -> List[str]:
        """读取或计算 `compatible_genres` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `compatible_genres` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `List[str]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return ["xuanhuan", "xianxia", "wuxia", "fantasy"]

    def on_beat_enhance(
        self,
        beat_description: str,
        beat_focus: str,
        chapter_number: int,
        outline: str,
    ) -> str:
        """同步执行 `on_beat_enhance` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `on_beat_enhance` 这一入口。
        关键输入:
        - beat_description: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - beat_focus: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - chapter_number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - outline: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if beat_focus in ("action", "martial_arts", "power_reveal") or \
           any(kw in beat_description for kw in ["战斗", "对决", "交锋", "过招", "攻击"]):
            return (
                "战斗编排增强提示：\n"
                "1. 动作分解：将一个回合拆成「起手→出招→碰撞→结果」四拍\n"
                "2. 感官层次：视觉（招式形态）+ 听觉（破空声）+ 触觉（力量反馈）\n"
                "3. 节奏控制：快慢交替——密集对攻后穿插喘息/对话/心理\n"
                "4. 避免流水账：不要逐招列举，抓住 2-3 个关键招式重点描写\n"
                "5. 旁观者视角：穿插围观者的反应来侧面烘托战斗激烈程度"
            )
        return ""

    def on_audit_enhance(
        self,
        chapter_number: int,
        chapter_content: str,
        outline: str,
    ) -> List[str]:
        """同步执行 `on_audit_enhance` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `on_audit_enhance` 这一入口。
        关键输入:
        - chapter_number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - chapter_content: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - outline: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        关键输出: `List[str]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        checks = []
        if any(kw in outline for kw in ["战斗", "对决", "比武", "交锋", "攻击"]):
            checks.append("检查战斗场景是否有具体的招式/动作描写（不能只有结果没有过程）")
            checks.append("检查战斗节奏是否有快慢变化（避免全程高强度或全程平淡）")
        return checks
