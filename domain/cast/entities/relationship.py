"""Relationship entity"""
from dataclasses import dataclass, field
from typing import List
from domain.cast.value_objects.relationship_id import RelationshipId
from domain.cast.value_objects.character_id import CharacterId
from domain.cast.entities.story_event import StoryEvent


@dataclass
class Relationship:
    """Relationship entity

    Represents a relationship between two characters in the cast graph.
    """

    id: RelationshipId
    source_id: CharacterId
    target_id: CharacterId
    label: str = ""
    note: str = ""
    directed: bool = True
    story_events: List[StoryEvent] = field(default_factory=list)

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if self.source_id == self.target_id:
            raise ValueError("Relationship cannot be between the same character")

    def add_story_event(self, event: StoryEvent) -> None:
        """Add a story event to the relationship

        Args:
            event: Story event to add
        """
        # Check if event with same ID already exists
        existing_ids = {e.id for e in self.story_events}
        if event.id in existing_ids:
            # Update existing event
            self.story_events = [e if e.id != event.id else event for e in self.story_events]
        else:
            self.story_events.append(event)

    def remove_story_event(self, event_id: str) -> None:
        """Remove a story event from the relationship

        Args:
            event_id: ID of the event to remove
        """
        self.story_events = [e for e in self.story_events if e.id != event_id]
