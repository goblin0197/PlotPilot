from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ForeshadowingStatus(str, Enum):
    """伏笔状态"""
    PLANTED = "planted"      # 已埋下
    RESOLVED = "resolved"    # 已解决
    ABANDONED = "abandoned"  # 已放弃


class ImportanceLevel(int, Enum):
    """重要性级别"""
    LOW = 1        # 低
    MEDIUM = 2     # 中等
    HIGH = 3       # 高
    CRITICAL = 4   # 关键


@dataclass(frozen=True)
class Foreshadowing:
    """伏笔值对象"""
    id: str
    planted_in_chapter: int
    description: str
    importance: ImportanceLevel
    status: ForeshadowingStatus
    suggested_resolve_chapter: Optional[int] = None
    resolved_in_chapter: Optional[int] = None

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if self.planted_in_chapter < 1:
            raise ValueError("planted_in_chapter must be >= 1")
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")
        if self.status == ForeshadowingStatus.RESOLVED and self.resolved_in_chapter is None:
            raise ValueError("RESOLVED status requires resolved_in_chapter")

        # Validate optional chapter fields
        if self.suggested_resolve_chapter is not None and self.suggested_resolve_chapter < 1:
            raise ValueError("suggested_resolve_chapter must be >= 1")
        if self.resolved_in_chapter is not None and self.resolved_in_chapter < 1:
            raise ValueError("resolved_in_chapter must be >= 1")

        # Validate business rules
        if self.resolved_in_chapter is not None and self.resolved_in_chapter < self.planted_in_chapter:
            raise ValueError("resolved_in_chapter must be >= planted_in_chapter")
        if self.suggested_resolve_chapter is not None and self.suggested_resolve_chapter < self.planted_in_chapter:
            raise ValueError("suggested_resolve_chapter must be >= planted_in_chapter")
