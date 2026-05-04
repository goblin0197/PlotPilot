"""SQLite Entity Base Repository 实现"""
import json
import logging
from typing import Optional
from uuid import uuid4
from domain.novel.repositories.entity_base_repository import EntityBaseRepository
from infrastructure.persistence.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SqliteEntityBaseRepository(EntityBaseRepository):
    """SQLite Entity Base Repository 实现"""

    def __init__(self, db: DatabaseConnection):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - db: 数据库连接或访问封装，用于执行持久化操作。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.db = db

    def get_by_id(self, entity_id: str) -> Optional[dict]:
        """根据 ID 获取实体基座

        Args:
            entity_id: 实体 ID

        Returns:
            实体字典，如果不存在返回 None
        """
        sql = "SELECT * FROM entity_base WHERE id = ?"
        row = self.db.fetch_one(sql, (entity_id,))

        if not row:
            return None

        entity = dict(row)
        # 反序列化 core_attributes JSON
        entity["core_attributes"] = json.loads(entity["core_attributes"])
        return entity

    def create(
        self,
        novel_id: str,
        entity_type: str,
        name: str,
        core_attributes: dict
    ) -> str:
        """创建新实体基座

        Args:
            novel_id: 小说 ID
            entity_type: 实体类型
            name: 实体名称
            core_attributes: 核心属性字典

        Returns:
            新创建的实体 ID
        """
        entity_id = str(uuid4())
        core_attributes_json = json.dumps(core_attributes, ensure_ascii=False)

        sql = """
            INSERT INTO entity_base (id, novel_id, entity_type, name, core_attributes)
            VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute(sql, (entity_id, novel_id, entity_type, name, core_attributes_json))
        self.db.get_connection().commit()

        logger.info(f"Created entity {entity_id} ({entity_type}: {name}) for novel {novel_id}")
        return entity_id
