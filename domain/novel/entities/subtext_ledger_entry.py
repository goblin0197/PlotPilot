# domain/novel/entities/subtext_ledger_entry.py
"""伏笔手账本条目（手动）：主角或读者当下的疑问，本阶段兑现即可，不必写长文。"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class SubtextLedgerEntry:
    """不可变值对象。"""

    id: str
    chapter: int
    character_id: str
    question: str
    status: str  # "pending" | "consumed"
    consumed_at_chapter: Optional[int] = None
    suggested_resolve_chapter: Optional[int] = None
    resolve_chapter_window: Optional[int] = None
    importance: str = "medium"
    created_at: datetime = None

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.utcnow())

        if self.status not in ("pending", "consumed"):
            raise ValueError(f"Invalid status: {self.status}. Must be 'pending' or 'consumed'")

        if self.status == "consumed" and self.consumed_at_chapter is None:
            raise ValueError("consumed_at_chapter must be set when status is 'consumed'")

        if self.status == "pending" and self.consumed_at_chapter is not None:
            raise ValueError("consumed_at_chapter must be None when status is 'pending'")

        valid_importance = ("low", "medium", "high", "critical")
        if self.importance not in valid_importance:
            raise ValueError(f"Invalid importance: {self.importance}. Must be one of {valid_importance}")

        if self.suggested_resolve_chapter is not None and self.suggested_resolve_chapter < self.chapter:
            raise ValueError("suggested_resolve_chapter must be >= chapter (埋入章节)")
