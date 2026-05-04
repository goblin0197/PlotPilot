from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActivityMetrics:
    """角色活动度指标值对象

    跟踪角色在小说中的活跃程度，用于智能角色选择。
    """

    last_appearance_chapter: int = 0
    appearance_count: int = 0
    total_dialogue_count: int = 0
    last_updated: datetime = None

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()

    def update_activity(self, chapter_number: int, dialogue_count: int = 0) -> None:
        """更新活动指标

        Args:
            chapter_number: 章节号
            dialogue_count: 对话数量（可选）
        """
        self.last_appearance_chapter = chapter_number
        self.appearance_count += 1
        self.total_dialogue_count += dialogue_count
        self.last_updated = datetime.utcnow()

    def is_active_since(self, chapter: int) -> bool:
        """判断角色是否在指定章节之后活跃

        Args:
            chapter: 章节号

        Returns:
            bool: 如果角色在该章节或之后出现过，返回 True
        """
        return self.last_appearance_chapter >= chapter
