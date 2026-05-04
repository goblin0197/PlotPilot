"""SQLite 节拍表仓储实现"""

import json
import uuid
from typing import Optional
from domain.novel.entities.beat_sheet import BeatSheet
from domain.novel.value_objects.scene import Scene
from domain.novel.repositories.beat_sheet_repository import BeatSheetRepository


class SqliteBeatSheetRepository(BeatSheetRepository):
    """SQLite 节拍表仓储实现

    使用 JSON Blob 存储节拍表数据
    """

    def __init__(self, db_connection):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - db_connection: 业务输入参数，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.db = db_connection

    async def save(self, beat_sheet: BeatSheet) -> None:
        """保存节拍表"""
        # 序列化场景列表
        scenes_data = [
            {
                "title": scene.title,
                "goal": scene.goal,
                "pov_character": scene.pov_character,
                "location": scene.location,
                "tone": scene.tone,
                "estimated_words": scene.estimated_words,
                "order_index": scene.order_index,
            }
            for scene in beat_sheet.scenes
        ]

        data = {
            "id": beat_sheet.id,
            "chapter_id": beat_sheet.chapter_id,
            "scenes": scenes_data,
            "created_at": beat_sheet.created_at.isoformat(),
            "updated_at": beat_sheet.updated_at.isoformat(),
        }

        conn = self.db.get_connection()
        payload = json.dumps(data)
        conn.execute(
            """
            INSERT INTO beat_sheets (id, chapter_id, data)
            VALUES (?, ?, ?)
            ON CONFLICT(chapter_id) DO UPDATE SET
                id = excluded.id,
                data = excluded.data,
                updated_at = CURRENT_TIMESTAMP
            """,
            (beat_sheet.id, beat_sheet.chapter_id, payload),
        )
        conn.commit()

    async def get_by_chapter_id(self, chapter_id: str) -> Optional[BeatSheet]:
        """根据章节 ID 获取节拍表"""
        cursor = self.db.execute(
            """
            SELECT data FROM beat_sheets
            WHERE chapter_id = ?
            """,
            (chapter_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        data = json.loads(row[0])

        # 反序列化场景列表
        scenes = [
            Scene(
                title=scene_data["title"],
                goal=scene_data["goal"],
                pov_character=scene_data["pov_character"],
                location=scene_data.get("location"),
                tone=scene_data.get("tone"),
                estimated_words=scene_data["estimated_words"],
                order_index=scene_data["order_index"],
            )
            for scene_data in data["scenes"]
        ]

        beat_sheet = BeatSheet(
            id=data["id"],
            chapter_id=data["chapter_id"],
            scenes=scenes
        )

        return beat_sheet

    async def delete_by_chapter_id(self, chapter_id: str) -> None:
        """删除章节的节拍表"""
        conn = self.db.get_connection()
        conn.execute(
            """
            DELETE FROM beat_sheets
            WHERE chapter_id = ?
            """,
            (chapter_id,)
        )
        conn.commit()

    async def exists(self, chapter_id: str) -> bool:
        """检查章节是否已有节拍表"""
        cursor = self.db.execute(
            """
            SELECT 1 FROM beat_sheets
            WHERE chapter_id = ?
            """,
            (chapter_id,)
        )
        return cursor.fetchone() is not None
