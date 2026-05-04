"""读者模拟反馈 DTO — 面向 API 层的序列化模型。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ReaderDimensionScoresDTO:
    """四维度评分"""
    suspense_retention: float = 50.0
    thrill_score: float = 50.0
    churn_risk: float = 30.0
    emotional_resonance: float = 50.0

    def to_dict(self) -> Dict[str, float]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, float]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "suspense_retention": round(self.suspense_retention, 1),
            "thrill_score": round(self.thrill_score, 1),
            "churn_risk": round(self.churn_risk, 1),
            "emotional_resonance": round(self.emotional_resonance, 1),
        }


@dataclass
class ReaderFeedbackDTO:
    """单个读者人设的反馈"""
    persona: str  # hardcore / casual / nitpicker
    persona_label: str  # 硬核粉 / 休闲读者 / 挑刺党
    scores: ReaderDimensionScoresDTO
    one_line_verdict: str = ""
    highlights: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "persona": self.persona,
            "persona_label": self.persona_label,
            "scores": self.scores.to_dict(),
            "one_line_verdict": self.one_line_verdict,
            "highlights": self.highlights,
            "pain_points": self.pain_points,
            "suggestions": self.suggestions,
        }


PERSONA_LABELS = {
    "hardcore": "硬核粉",
    "casual": "休闲读者",
    "nitpicker": "挑刺党",
}


@dataclass
class ChapterReaderReportDTO:
    """章节级读者模拟报告"""
    novel_id: str
    chapter_number: int
    feedbacks: List[ReaderFeedbackDTO] = field(default_factory=list)
    overall_readability: float = 50.0
    chapter_hook_strength: str = "medium"
    pacing_verdict: str = ""
    analyzed_at: Optional[datetime] = None
    # 降级标识：True 表示 LLM 调用失败或解析失败，所有评分为默认值
    # 该字段用于 API 层判断是否持久化、返回什么 HTTP 状态码
    is_fallback: bool = False
    # 降级原因（仅 is_fallback=True 时填充）
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "novel_id": self.novel_id,
            "chapter_number": self.chapter_number,
            "feedbacks": [f.to_dict() for f in self.feedbacks],
            "overall_readability": round(self.overall_readability, 1),
            "chapter_hook_strength": self.chapter_hook_strength,
            "pacing_verdict": self.pacing_verdict,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            # 便捷聚合：三个读者的平均分
            "avg_scores": self._compute_avg_scores(),
            "is_fallback": self.is_fallback,
            "error_message": self.error_message,
        }

    def _compute_avg_scores(self) -> Dict[str, float]:
        """同步执行 `_compute_avg_scores` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_compute_avg_scores` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, float]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if not self.feedbacks:
            return {
                "suspense_retention": 0, "thrill_score": 0,
                "churn_risk": 0, "emotional_resonance": 0,
            }
        n = len(self.feedbacks)
        return {
            "suspense_retention": round(sum(f.scores.suspense_retention for f in self.feedbacks) / n, 1),
            "thrill_score": round(sum(f.scores.thrill_score for f in self.feedbacks) / n, 1),
            "churn_risk": round(sum(f.scores.churn_risk for f in self.feedbacks) / n, 1),
            "emotional_resonance": round(sum(f.scores.emotional_resonance for f in self.feedbacks) / n, 1),
        }
