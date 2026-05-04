"""时间线注册表实体"""
from typing import List, Optional
from domain.shared.base_entity import BaseEntity
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.timeline_event import TimelineEvent


class TimelineRegistry(BaseEntity):
    """时间线注册表

    管理小说中所有时间线事件，支持绝对时间、相对时间和模糊时间
    """

    def __init__(
        self,
        id: str,
        novel_id: NovelId,
        events: Optional[List[TimelineEvent]] = None
    ):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - id: 业务标识或配置键，用于定位目标记录。
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - events: `Optional[List[TimelineEvent]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        super().__init__(id)
        self.novel_id = novel_id
        self.events: List[TimelineEvent] = events if events is not None else []

    def add_event(self, event: TimelineEvent) -> None:
        """添加时间线事件"""
        if event is None:
            raise ValueError("TimelineEvent cannot be None")
        self.events.append(event)

    def get_events_by_chapter(self, chapter_number: int) -> List[TimelineEvent]:
        """获取指定章节的所有事件"""
        return [e for e in self.events if e.chapter_number == chapter_number]

    def get_events_by_type(self, timestamp_type: str) -> List[TimelineEvent]:
        """按时间类型筛选事件（absolute/relative/vague）"""
        return [e for e in self.events if e.timestamp_type == timestamp_type]

    def get_all_events_sorted(self) -> List[TimelineEvent]:
        """获取所有事件，按章节号排序"""
        return sorted(self.events, key=lambda e: e.chapter_number)
