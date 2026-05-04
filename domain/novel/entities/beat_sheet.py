"""节拍表实体

节拍表（Beat Sheet）是章节的场景列表，用于指导正文生成
"""

from typing import List
from domain.shared.base_entity import BaseEntity
from domain.novel.value_objects.scene import Scene


class BeatSheet(BaseEntity):
    """节拍表实体

    包含章节的所有场景，按顺序排列
    """

    def __init__(
        self,
        id: str,
        chapter_id: str,
        scenes: List[Scene]
    ):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - id: 业务标识或配置键，用于定位目标记录。
        - chapter_id: 业务标识或配置键，用于定位目标记录。
        - scenes: `List[Scene]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        super().__init__(id)
        self.chapter_id = chapter_id
        self.scenes = scenes

    def get_scene_count(self) -> int:
        """获取场景数量"""
        return len(self.scenes)

    def get_total_estimated_words(self) -> int:
        """获取预估总字数"""
        return sum(scene.estimated_words for scene in self.scenes)

    def get_scene_by_index(self, index: int) -> Scene:
        """按索引获取场景"""
        if index < 0 or index >= len(self.scenes):
            raise IndexError(f"Scene index {index} out of range")
        return self.scenes[index]

    def validate(self) -> bool:
        """验证节拍表"""
        if not self.scenes:
            raise ValueError("Beat sheet must have at least one scene")

        # 验证场景顺序
        for i, scene in enumerate(self.scenes):
            if scene.order_index != i:
                raise ValueError(f"Scene order mismatch: expected {i}, got {scene.order_index}")

        return True
