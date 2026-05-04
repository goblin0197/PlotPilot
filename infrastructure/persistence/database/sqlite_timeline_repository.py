"""SQLite 时间线仓储实现"""
import json
import logging
from typing import Optional
from domain.novel.repositories.timeline_repository import TimelineRepository
from domain.novel.entities.timeline_registry import TimelineRegistry
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.timeline_event import TimelineEvent
from infrastructure.persistence.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SqliteTimelineRepository(TimelineRepository):
    """SQLite 时间线仓储实现

    使用 JSON Blob 存储时间线事件列表
    """

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
        self._ensure_table()

    def _ensure_table(self) -> None:
        """确保表存在"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS timeline_registries (
                novel_id TEXT PRIMARY KEY,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn = self.db.get_connection()
        conn.commit()

    def save(self, registry: TimelineRegistry) -> None:
        """保存时间线注册表"""
        data = {
            "id": registry.id,
            "novel_id": registry.novel_id.value,
            "events": [
                {
                    "id": e.id,
                    "chapter_number": e.chapter_number,
                    "event": e.event,
                    "timestamp": e.timestamp,
                    "timestamp_type": e.timestamp_type
                }
                for e in registry.events
            ]
        }

        conn = self.db.get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO timeline_registries (novel_id, data, updated_at) VALUES (?, json(?), CURRENT_TIMESTAMP)",
            (registry.novel_id.value, json.dumps(data))
        )
        conn.commit()
        logger.debug(f"Saved TimelineRegistry for novel {registry.novel_id.value}")

    def get_by_novel_id(self, novel_id: NovelId) -> Optional[TimelineRegistry]:
        """根据小说ID获取时间线注册表"""
        cursor = self.db.execute(
            "SELECT data FROM timeline_registries WHERE novel_id = ?",
            (novel_id.value,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        data = json.loads(row[0])
        events = [
            TimelineEvent(
                id=e["id"],
                chapter_number=e["chapter_number"],
                event=e["event"],
                timestamp=e["timestamp"],
                timestamp_type=e["timestamp_type"]
            )
            for e in data.get("events", [])
        ]

        return TimelineRegistry(
            id=data["id"],
            novel_id=NovelId(data["novel_id"]),
            events=events
        )

    def delete(self, novel_id: NovelId) -> None:
        """删除时间线注册表"""
        conn = self.db.get_connection()
        conn.execute(
            "DELETE FROM timeline_registries WHERE novel_id = ?",
            (novel_id.value,)
        )
        conn.commit()
        logger.debug(f"Deleted TimelineRegistry for novel {novel_id.value}")
