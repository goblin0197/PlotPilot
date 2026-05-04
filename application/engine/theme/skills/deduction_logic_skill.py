"""推理逻辑校验 Skill — 为悬疑/推理题材提供公平推理原则的增强

确保线索布置符合推理公平原则，关键证据在揭露前已出现。
"""

from typing import List
from application.engine.theme.theme_agent import ThemeSkill


class DeductionLogicSkill(ThemeSkill):
    """推理逻辑校验器 — 确保推理链完整、线索公平"""

    @property
    def skill_key(self) -> str:
        """读取或计算 `skill_key` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_key` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "deduction_logic"

    @property
    def skill_name(self) -> str:
        """读取或计算 `skill_name` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_name` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "推理逻辑"

    @property
    def skill_description(self) -> str:
        """读取或计算 `skill_description` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_description` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return "确保推理链条完整自洽、线索布置符合公平推理原则、红鲱鱼自然不刻意"

    @property
    def compatible_genres(self) -> List[str]:
        """读取或计算 `compatible_genres` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `compatible_genres` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `List[str]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return ["suspense"]

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
            "推理公平原则检查清单：\n"
            "1. 每条关键线索必须在真相揭露前至少出现过一次\n"
            "2. 红鲱鱼必须有独立的合理解释，不能事后被无视\n"
            "3. 推理链：观察 → 假设 → 验证 → 排除 → 结论，不可跳步\n"
            "4. 凶手/真相的动机必须在前文有过暗示或铺垫\n"
            "5. 时间线、不在场证明等关键要素必须经得起回溯验证"
        )

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
        if any(kw in chapter_content for kw in ["真相", "揭露", "凶手", "破案", "推理"]):
            checks.append("检查揭露的真相是否在前文有充分的线索铺垫（公平原则）")
            checks.append("检查推理链是否有逻辑跳跃或缺失环节")
        return checks
