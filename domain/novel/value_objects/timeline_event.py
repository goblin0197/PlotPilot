"""时间线事件值对象"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TimelineEvent:
    """时间线事件

    记录小说中发生的事件及其时间戳
    """
    id: str
    chapter_number: int
    event: str  # 事件描述
    timestamp: str  # 时间戳（如"第三年春"、"2024-03-15"、"午夜"）
    timestamp_type: str  # 时间类型：absolute/relative/vague

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if self.chapter_number < 1:
            raise ValueError("chapter_number must be >= 1")
        if not self.event or not self.event.strip():
            raise ValueError("event cannot be empty")
        if not self.timestamp or not self.timestamp.strip():
            raise ValueError("timestamp cannot be empty")
        if self.timestamp_type not in ("absolute", "relative", "vague"):
            raise ValueError("timestamp_type must be one of: absolute, relative, vague")
