from typing import List, Any
from domain.shared.base_entity import BaseEntity
from domain.bible.value_objects.character_id import CharacterId
from domain.shared.exceptions import InvalidOperationError


class Character(BaseEntity):
    """人物实体

    支持 POV 防火墙：
    - public_profile: 公开信息，总是可见
    - hidden_profile: 隐藏信息（如卧底身份），仅在 reveal_chapter 后可见
    - reveal_chapter: 揭示章节号，None 表示总是可见
    """

    def __init__(
        self,
        id: CharacterId,
        name: str,
        description: str,
        relationships: List[Any] = None,
        public_profile: str = "",
        hidden_profile: str = "",
        reveal_chapter: int = None,
        mental_state: str = "NORMAL",
        verbal_tic: str = "",
        idle_behavior: str = "",
    ):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - id: 业务标识或配置键，用于定位目标记录。
        - name: 业务标识或配置键，用于定位目标记录。
        - description: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - relationships: `List[Any]` 类型的业务输入，参与本函数的主要计算或流程控制。
        - public_profile: 文件系统路径，函数会据此读取、写入或定位资源。
        - hidden_profile: 文件系统路径，函数会据此读取、写入或定位资源。
        - reveal_chapter: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - mental_state: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - verbal_tic: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - idle_behavior: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        super().__init__(id.value)
        self.character_id = id
        self.name = name
        self.description = description
        self.relationships = relationships or []
        self.public_profile = public_profile
        self.hidden_profile = hidden_profile
        self.reveal_chapter = reveal_chapter
        self.mental_state = mental_state or "NORMAL"
        self.verbal_tic = verbal_tic or ""
        self.idle_behavior = idle_behavior or ""

        # 验证 reveal_chapter
        if self.reveal_chapter is not None and self.reveal_chapter < 1:
            raise ValueError(f"reveal_chapter must be >= 1, got {self.reveal_chapter}")

    def add_relationship(self, relationship: Any) -> None:
        """添加关系（字符串或结构化 dict，与 Bible JSON / LLM 一致）"""
        if relationship in self.relationships:
            raise InvalidOperationError(f"Relationship already exists: {relationship}")
        self.relationships.append(relationship)

    def remove_relationship(self, relationship: str) -> None:
        """删除关系"""
        if relationship not in self.relationships:
            raise InvalidOperationError(f"Relationship not found: {relationship}")
        self.relationships.remove(relationship)

    def update_description(self, description: str) -> None:
        """更新描述"""
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        self.description = description
