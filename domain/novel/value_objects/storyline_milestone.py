from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class StorylineMilestone:
    """故事线里程碑值对象"""
    order: int
    title: str
    description: str
    target_chapter_start: int
    target_chapter_end: int
    prerequisites: List[str]
    triggers: List[str]

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if self.order < 0:
            raise ValueError("Order must be non-negative")

        if self.target_chapter_start < 1 or self.target_chapter_end < 1:
            raise ValueError("Chapter numbers must be positive")

        if self.target_chapter_end < self.target_chapter_start:
            raise ValueError("target_chapter_end must be >= target_chapter_start")
