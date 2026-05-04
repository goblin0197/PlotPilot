"""修炼体系 Skill — 为修仙/玄幻题材提供修炼境界体系的上下文增强

示例 Skill 实现，演示 ThemeSkill 的使用方式。
可被玄幻（xuanhuan）和仙侠（xianxia）题材共享。
"""

from typing import List
from application.engine.theme.theme_agent import ThemeSkill


class CultivationSystemSkill(ThemeSkill):
    """修炼体系生成器 — 注入修炼境界参考到写作上下文"""

    @property
    def skill_key(self) -> str:
        """读取或计算 `skill_key` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_key` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "cultivation_system"

    @property
    def skill_name(self) -> str:
        """读取或计算 `skill_name` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_name` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "修炼体系"

    @property
    def skill_description(self) -> str:
        """读取或计算 `skill_description` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_description` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "注入标准修炼境界参考（练气→筑基→…→大乘→渡劫），确保全书境界描写一致"

    # ─── 适用题材 ───

    @property
    def compatible_genres(self) -> List[str]:
        """声明此 Skill 适用的题材 genre_key 列表"""
        return ["xuanhuan", "xianxia"]

    # ─── 注入点实现 ───

    def on_context_build(
        self,
        novel_id: str,
        chapter_number: int,
        outline: str,
        existing_context: str,
    ) -> str:
        """同步执行 `on_context_build` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `on_context_build` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - chapter_number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - outline: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - existing_context: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return (
            "修炼境界体系（由低到高）：\n"
            "练气期 → 筑基期 → 金丹期 → 元婴期 → "
            "化神期 → 合体期 → 大乘期 → 渡劫期\n"
            "每个大境界分初期/中期/后期/巅峰四个小阶段。\n"
            "突破大境界需要天劫/心魔/特殊机缘，不可随意跳级。\n"
            "请确保角色的境界描写前后一致，不要出现境界倒退或跳跃。"
        )

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
        if beat_focus == "cultivation" or "突破" in beat_description or "修炼" in beat_description:
            return (
                "修炼/突破场景增强提示：描写灵气在经脉中的具体流动路径、"
                "丹田/识海的变化、突破瓶颈时的身体反应和天地异象。"
                "参照上方境界体系确认当前角色的境界。"
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
        if any(kw in chapter_content for kw in ["突破", "晋升", "渡劫", "筑基", "金丹", "元婴"]):
            checks.append("检查境界描写是否与全书体系一致（不可跳级、不可倒退）")
        return checks
