from dataclasses import dataclass


@dataclass(frozen=True)
class ChapterContent:
    """章节内容值对象"""
    raw_text: str

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if not self.raw_text or not self.raw_text.strip():
            raise ValueError("Chapter content cannot be None or empty")

    def word_count(self) -> int:
        """计算字数（简单实现）"""
        return len(self.raw_text)

    def __str__(self) -> str:
        """同步执行 `__str__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__str__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        preview_length = 50
        if len(self.raw_text) <= preview_length:
            return self.raw_text
        return f"{self.raw_text[:preview_length]}..."
