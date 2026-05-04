"""多维张力分析结果值对象。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TensionDimensions:
    """多维张力分析结果（所有分值范围 0-100）。

    Attributes:
        plot_tension: 情节张力 — 冲突烈度、悬念密度、信息不对称
        emotional_tension: 情绪张力 — 角色情绪波动、读者共情深度
        pacing_tension: 节奏张力 — 场景切换频率、叙述节奏、信息密度
        composite_score: 综合张力 — 加权汇总（plot 40%, emotional 30%, pacing 30%）
    """

    plot_tension: float
    emotional_tension: float
    pacing_tension: float
    composite_score: float

    # 权重：情节 > 情绪 = 节奏
    _WEIGHTS = (0.40, 0.30, 0.30)

    def __post_init__(self) -> None:
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `TypeError, ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        for name in (
            "plot_tension",
            "emotional_tension",
            "pacing_tension",
            "composite_score",
        ):
            val = getattr(self, name)
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be numeric, got {type(val).__name__}")
            if not (0.0 <= float(val) <= 100.0):
                raise ValueError(f"{name} must be 0-100, got {val}")

    @classmethod
    def from_raw_scores(
        cls,
        plot: float,
        emotional: float,
        pacing: float,
    ) -> TensionDimensions:
        """从三个维度原始分值构造实例，自动计算加权综合分。"""
        plot = max(0.0, min(100.0, float(plot)))
        emotional = max(0.0, min(100.0, float(emotional)))
        pacing = max(0.0, min(100.0, float(pacing)))
        composite = round(
            plot * cls._WEIGHTS[0]
            + emotional * cls._WEIGHTS[1]
            + pacing * cls._WEIGHTS[2],
            1,
        )
        return cls(
            plot_tension=plot,
            emotional_tension=emotional,
            pacing_tension=pacing,
            composite_score=composite,
        )

    @classmethod
    def neutral(cls) -> TensionDimensions:
        """返回全维度 50.0 的中性结果（用于兜底）。"""
        return cls(50.0, 50.0, 50.0, 50.0)
