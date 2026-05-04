"""Writer Block 数据传输对象"""
from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TensionSlingshotRequest(BaseModel):
    """张力弹弓请求：与 POST JSON body 一致，由 FastAPI / Pydantic 做校验。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    novel_id: str = Field(..., min_length=1, description="小说 ID，须与路径参数一致")
    chapter_number: int = Field(..., ge=1, description="目标章节序号")
    stuck_reason: Optional[str] = Field(
        default=None,
        description="作者自述的卡文原因，可选",
    )

    @field_validator("stuck_reason", mode="before")
    @classmethod
    def empty_stuck_reason_to_none(cls, value: object) -> Optional[str]:
        """校验 `empty_stuck_reason_none` 的输入边界并返回规范化结果。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `empty_stuck_reason_to_none` 这一入口。
        关键输入:
        - value: 待校验、转换或写入的值，类型约束为 `object`。
        关键输出: `Optional[str]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


@dataclass
class TensionDiagnosis:
    """张力诊断结果 DTO"""
    diagnosis: str
    tension_level: str  # low/medium/high
    missing_elements: List[str]
    suggestions: List[str]
