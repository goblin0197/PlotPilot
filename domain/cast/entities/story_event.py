"""Story Event entity"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class StoryEvent:
    """Story Event entity

    Represents a milestone or key event in the story timeline.
    """

    id: str
    summary: str
    chapter_id: Optional[int] = None
    importance: str = "normal"  # "normal" or "key"

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if not self.id or not self.id.strip():
            raise ValueError("Story event ID cannot be empty")
        if not self.summary or not self.summary.strip():
            raise ValueError("Story event summary cannot be empty")
        if self.importance not in ["normal", "key"]:
            raise ValueError("Story event importance must be 'normal' or 'key'")
