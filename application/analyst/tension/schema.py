"""张力诊断 LLM 输出的 Pydantic 模型。"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TensionDiagnosisLlmPayload(BaseModel):
    """与 prompt 约定的 JSON 字段一致；额外字段忽略。"""

    model_config = ConfigDict(extra="ignore")

    diagnosis: str
    tension_level: str
    missing_elements: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

    @field_validator("tension_level", mode="before")
    @classmethod
    def normalize_tension_level(cls, value: object) -> str:
        """将常见别名与中文档位归一为 low / medium / high。"""
        if value is None:
            return "low"

        raw = str(value).strip()
        lower = raw.lower()

        direct = {
            "low": "low",
            "l": "low",
            "1": "low",
            "medium": "medium",
            "mid": "medium",
            "m": "medium",
            "2": "medium",
            "high": "high",
            "h": "high",
            "peak": "high",
            "3": "high",
            "4": "high",
        }
        if lower in direct:
            return direct[lower]

        if "低" in raw:
            return "low"
        if "中" in raw:
            return "medium"
        if "高" in raw or "峰值" in raw:
            return "high"

        return "medium"

    @field_validator("diagnosis", mode="before")
    @classmethod
    def strip_diagnosis(cls, value: object) -> str:
        """校验 `strip_diagnosis` 的输入边界并返回规范化结果。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `strip_diagnosis` 这一入口。
        关键输入:
        - value: 待校验、转换或写入的值，类型约束为 `object`。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if value is None:
            return ""
        return str(value).strip()
