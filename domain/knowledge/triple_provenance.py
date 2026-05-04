"""三元组与章节元素/结构节点之间的显式溯源（推断证据链）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TripleProvenanceRecord:
    """单条证据：关联 story_node（章节结构节点）与可选的 chapter_element 行。"""

    rule_id: str
    story_node_id: Optional[str] = None
    chapter_element_id: Optional[str] = None
    role: str = "primary"

    def to_row_dict(self, novel_id: str, triple_id: str, row_id: str) -> Dict[str, Any]:
        """同步转换或规范化 `row_dict` 相关的数据结构。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `to_row_dict` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - triple_id: 业务标识或配置键，用于定位目标记录。
        - row_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "id": row_id,
            "triple_id": triple_id,
            "novel_id": novel_id,
            "story_node_id": self.story_node_id,
            "chapter_element_id": self.chapter_element_id,
            "rule_id": self.rule_id,
            "role": self.role,
        }
