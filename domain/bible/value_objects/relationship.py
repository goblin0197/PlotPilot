from dataclasses import dataclass
from enum import Enum


class RelationType(Enum):
    """关系类型枚举"""
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    LOVER = "lover"
    ENEMY = "enemy"
    RIVAL = "rival"
    FAMILY = "family"


@dataclass(frozen=True)
class Relationship:
    """角色关系值对象"""
    relation_type: RelationType
    established_in_chapter: int
    description: str

    def __post_init__(self):
        # Validate relation_type is actually a RelationType enum
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `TypeError, ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if not isinstance(self.relation_type, RelationType):
            raise TypeError(f"relation_type must be a RelationType enum, got {type(self.relation_type).__name__}")

        # Validate description is a string
        if not isinstance(self.description, str):
            raise TypeError(f"description must be a string, got {type(self.description).__name__}")

        if self.established_in_chapter < 1:
            raise ValueError("established_in_chapter must be >= 1")
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")
