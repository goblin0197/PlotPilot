# domain/ai/value_objects/prompt.py
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class Prompt:
    """提示词值对象"""
    system: str
    user: str

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if not self.user or not self.user.strip():
            raise ValueError("User message cannot be empty")
        if not self.system or not self.system.strip():
            raise ValueError("System message cannot be empty")

    def to_messages(self) -> List[Dict[str, Any]]:
        """转换为消息列表格式"""
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": self.user})
        return messages
