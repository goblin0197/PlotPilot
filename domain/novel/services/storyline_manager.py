import uuid
from typing import List
from domain.novel.entities.storyline import Storyline
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.storyline_type import StorylineType
from domain.novel.value_objects.storyline_status import StorylineStatus
from domain.novel.value_objects.storyline_milestone import StorylineMilestone
from domain.novel.repositories.storyline_repository import StorylineRepository


class StorylineManager:
    """故事线管理领域服务"""

    def __init__(self, repository: StorylineRepository):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - repository: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.repository = repository

    def create_storyline(
        self,
        novel_id: NovelId,
        storyline_type: StorylineType,
        estimated_chapter_start: int,
        estimated_chapter_end: int,
        name: str = "",
        description: str = "",
    ) -> Storyline:
        """创建新的故事线

        Args:
            novel_id: 小说 ID
            storyline_type: 故事线类型
            estimated_chapter_start: 预计开始章节
            estimated_chapter_end: 预计结束章节
            name: 显示名称（可选）
            description: 详细说明（可选）

        Returns:
            创建的故事线实体
        """
        storyline_id = str(uuid.uuid4())
        storyline = Storyline(
            id=storyline_id,
            novel_id=novel_id,
            storyline_type=storyline_type,
            status=StorylineStatus.ACTIVE,
            estimated_chapter_start=estimated_chapter_start,
            estimated_chapter_end=estimated_chapter_end,
            name=name or "",
            description=description or "",
        )

        self.repository.save(storyline)
        return storyline

    def get_pending_milestones(self, storyline_id: str) -> List[StorylineMilestone]:
        """获取故事线的待完成里程碑

        Args:
            storyline_id: 故事线 ID

        Returns:
            待完成的里程碑列表

        Raises:
            ValueError: 如果故事线不存在
        """
        storyline = self.repository.get_by_id(storyline_id)
        if storyline is None:
            raise ValueError(f"Storyline {storyline_id} not found")

        return storyline.get_pending_milestones()

    def complete_milestone(self, storyline_id: str, milestone_order: int) -> None:
        """完成故事线的里程碑

        Args:
            storyline_id: 故事线 ID
            milestone_order: 里程碑顺序号

        Raises:
            ValueError: 如果故事线不存在或里程碑无效
        """
        storyline = self.repository.get_by_id(storyline_id)
        if storyline is None:
            raise ValueError(f"Storyline {storyline_id} not found")

        storyline.complete_milestone(milestone_order)
        self.repository.save(storyline)

    def get_storyline_context(self, storyline_id: str) -> str:
        """获取故事线上下文信息

        Args:
            storyline_id: 故事线 ID

        Returns:
            故事线上下文的文本描述

        Raises:
            ValueError: 如果故事线不存在
        """
        storyline = self.repository.get_by_id(storyline_id)
        if storyline is None:
            raise ValueError(f"Storyline {storyline_id} not found")

        context_parts = [
            f"Storyline Type: {storyline.storyline_type.value}",
            f"Status: {storyline.status.value}",
            f"Estimated Chapters: {storyline.estimated_chapter_start}-{storyline.estimated_chapter_end}"
        ]

        current_milestone = storyline.get_current_milestone()
        if current_milestone:
            context_parts.append(f"\nCurrent Milestone: {current_milestone.title}")
            context_parts.append(f"Description: {current_milestone.description}")
            context_parts.append(f"Target Chapters: {current_milestone.target_chapter_start}-{current_milestone.target_chapter_end}")
            if current_milestone.prerequisites:
                context_parts.append(f"Prerequisites: {', '.join(current_milestone.prerequisites)}")
            if current_milestone.triggers:
                context_parts.append(f"Triggers: {', '.join(current_milestone.triggers)}")
        else:
            context_parts.append("\nNo current milestone")

        return "\n".join(context_parts)
