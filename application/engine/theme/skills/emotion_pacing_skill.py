"""情感节奏 Skill — 为言情/情感线提供甜虐节奏控制的增强

适用于言情题材及任何有重要感情线的题材。
"""

from typing import List
from application.engine.theme.theme_agent import ThemeSkill


class EmotionPacingSkill(ThemeSkill):
    """情感节奏控制器 — 控制甜虐交替、避免情感疲劳"""

    @property
    def skill_key(self) -> str:
        """读取或计算 `skill_key` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_key` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "emotion_pacing"

    @property
    def skill_name(self) -> str:
        """读取或计算 `skill_name` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_name` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "情感节奏"

    @property
    def skill_description(self) -> str:
        """读取或计算 `skill_description` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_description` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "控制甜蜜/虐心的交替节奏，避免连续甜腻或连续虐心导致读者疲劳"

    @property
    def compatible_genres(self) -> List[str]:
        """读取或计算 `compatible_genres` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `compatible_genres` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `List[str]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return ["romance"]

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
        if beat_focus in ("romantic_tension", "inner_monologue", "emotion"):
            return (
                "情感节奏增强提示：\n"
                "1. 甜后埋刺：甜蜜场景结尾留一个微小的不安/隐患\n"
                "2. 虐中有暖：虐心场景中穿插对方默默付出的细节\n"
                "3. 心理真实：角色不会突然想通一切，犹豫和反复是真实的\n"
                "4. 感官描写：心动通过具体的身体反应呈现（心跳、脸红、不敢对视）"
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
        if any(kw in outline for kw in ["感情", "暧昧", "告白", "分手", "误会"]):
            checks.append("检查情感发展是否有过渡铺垫（不能突然心动或突然放弃）")
        return checks
