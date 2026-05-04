"""SQLite Bible 仓储：Bible 聚合与子表全部落库。"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from domain.bible.entities.bible import Bible
from domain.bible.repositories.bible_repository import BibleRepository
from domain.novel.value_objects.novel_id import NovelId
from infrastructure.persistence.database.connection import DatabaseConnection
from infrastructure.persistence.mappers.bible_mapper import BibleMapper

logger = logging.getLogger(__name__)


class SqliteBibleRepository(BibleRepository):
    """Bible 与子实体读写 SQLite；save 为整本替换子表。"""

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

    def _conn(self):
        """同步执行 `_conn` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_conn` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self.db.get_connection()

    def _now(self) -> str:
        """同步执行 `_now` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_now` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return datetime.utcnow().isoformat()

    def _clear_children(self, conn, novel_id: str) -> None:
        """同步执行 `_clear_children` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_clear_children` 这一入口。
        关键输入:
        - conn: 数据库连接或访问封装，用于执行持久化操作。
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        conn.execute("DELETE FROM bible_style_notes WHERE novel_id = ?", (novel_id,))
        conn.execute("DELETE FROM bible_timeline_notes WHERE novel_id = ?", (novel_id,))
        conn.execute("DELETE FROM bible_locations WHERE novel_id = ?", (novel_id,))
        conn.execute("DELETE FROM bible_world_settings WHERE novel_id = ?", (novel_id,))
        conn.execute("DELETE FROM bible_characters WHERE novel_id = ?", (novel_id,))

    def save(self, bible: Bible) -> None:
        """同步执行 `save` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `save` 这一入口。
        关键输入:
        - bible: `Bible` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        novel_id = bible.novel_id.value
        now = self._now()
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO bibles (id, novel_id, schema_version, extensions, created_at, updated_at)
                VALUES (?, ?, 1, '{}', ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    novel_id = excluded.novel_id,
                    updated_at = excluded.updated_at
                """,
                (bible.id, novel_id, now, now),
            )
            self._clear_children(conn, novel_id)

            for char in bible.characters:
                cid = char.character_id.value
                ms = getattr(char, "mental_state", None) or "NORMAL"
                vt = getattr(char, "verbal_tic", None) or ""
                ib = getattr(char, "idle_behavior", None) or ""
                conn.execute(
                    """
                    INSERT OR REPLACE INTO bible_characters (
                        id, novel_id, name, description,
                        mental_state, mental_state_reason, verbal_tic, idle_behavior,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (cid, novel_id, char.name, char.description or "", ms, "", vt, ib, now, now),
                )
                for i, rel in enumerate(char.relationships or []):
                    rid = f"{cid}-rel-{i}-{uuid.uuid4().hex[:6]}"
                    if isinstance(rel, str):
                        target_name = rel
                        relation = ""
                        description = ""
                    else:
                        # 支持 Pydantic 模型和字典两种格式
                        if hasattr(rel, "model_dump"):
                            rel_dict = rel.model_dump()
                        elif hasattr(rel, "dict"):
                            rel_dict = rel.dict()
                        else:
                            rel_dict = rel
                        target_name = rel_dict.get("target", "") or ""
                        relation = rel_dict.get("relation", "") or ""
                        description = rel_dict.get("description", "") or ""
                    conn.execute(
                        """
                        INSERT INTO bible_character_relationships
                        (id, character_id, target_name, relation, description)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (rid, cid, target_name, relation, description),
                    )

            for ws in bible.world_settings:
                conn.execute(
                    """
                    INSERT INTO bible_world_settings
                    (id, novel_id, name, description, setting_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ws.id,
                        novel_id,
                        ws.name,
                        ws.description or "",
                        ws.setting_type or "other",
                        now,
                        now,
                    ),
                )

            for loc in bible.locations:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO bible_locations
                    (id, novel_id, name, description, location_type, parent_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        loc.id,
                        novel_id,
                        loc.name,
                        loc.description or "",
                        loc.location_type or "other",
                        loc.parent_id,
                        now,
                        now,
                    ),
                )

            for order, note in enumerate(bible.timeline_notes):
                conn.execute(
                    """
                    INSERT INTO bible_timeline_notes
                    (id, novel_id, event, time_point, description, sort_order, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        note.id,
                        novel_id,
                        note.event or "",
                        note.time_point or "",
                        note.description or "",
                        order,
                        now,
                        now,
                    ),
                )

            for sn in bible.style_notes:
                conn.execute(
                    """
                    INSERT INTO bible_style_notes
                    (id, novel_id, category, content, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (sn.id, novel_id, sn.category, sn.content or "", now, now),
                )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _character_rows(self, novel_id: str) -> List[Dict[str, Any]]:
        """同步执行 `_character_rows` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_character_rows` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[Dict[str, Any]]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        return self.db.fetch_all(
            "SELECT * FROM bible_characters WHERE novel_id = ? ORDER BY id",
            (novel_id,),
        )

    def _rels_for_character(self, character_id: str) -> List[Dict[str, str]]:
        """同步执行 `_rels_for_character` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_rels_for_character` 这一入口。
        关键输入:
        - character_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[Dict[str, str]]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self.db.fetch_all(
            """
            SELECT target_name, relation, description
            FROM bible_character_relationships
            WHERE character_id = ?
            ORDER BY id
            """,
            (character_id,),
        )
        return [
            {
                "target": r["target_name"],
                "relation": r["relation"],
                "description": r["description"],
            }
            for r in rows
        ]

    def _to_mapper_dict(self, bible_id: str, novel_id: str) -> Dict[str, Any]:
        """同步执行 `_to_mapper_dict` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_to_mapper_dict` 这一入口。
        关键输入:
        - bible_id: 业务标识或配置键，用于定位目标记录。
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        chars_out: List[Dict[str, Any]] = []
        for row in self._character_rows(novel_id):
            cid = row["id"]
            chars_out.append(
                {
                    "id": cid,
                    "name": row["name"],
                    "description": row["description"] or "",
                    "relationships": self._rels_for_character(cid),
                    "mental_state": row.get("mental_state") or "NORMAL",
                    "verbal_tic": row.get("verbal_tic") or "",
                    "idle_behavior": row.get("idle_behavior") or "",
                }
            )

        ws_rows = self.db.fetch_all(
            "SELECT * FROM bible_world_settings WHERE novel_id = ? ORDER BY id",
            (novel_id,),
        )
        world_settings = [
            {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"] or "",
                "setting_type": r["setting_type"] or "other",
            }
            for r in ws_rows
        ]

        loc_rows = self.db.fetch_all(
            "SELECT * FROM bible_locations WHERE novel_id = ? ORDER BY id",
            (novel_id,),
        )
        locations: List[Dict[str, Any]] = []
        for r in loc_rows:
            item: Dict[str, Any] = {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"] or "",
                "location_type": r["location_type"] or "other",
            }
            if r.get("parent_id"):
                item["parent_id"] = r["parent_id"]
            locations.append(item)

        tn_rows = self.db.fetch_all(
            """
            SELECT id, event, time_point, description
            FROM bible_timeline_notes
            WHERE novel_id = ?
            ORDER BY sort_order, id
            """,
            (novel_id,),
        )
        timeline_notes = [
            {
                "id": r["id"],
                "event": r["event"] or "",
                "time_point": r["time_point"] or "",
                "description": r["description"] or "",
            }
            for r in tn_rows
        ]

        sn_rows = self.db.fetch_all(
            "SELECT id, category, content FROM bible_style_notes WHERE novel_id = ? ORDER BY id",
            (novel_id,),
        )
        style_notes = [
            {"id": r["id"], "category": r["category"], "content": r["content"] or ""}
            for r in sn_rows
        ]

        return {
            "id": bible_id,
            "novel_id": novel_id,
            "characters": chars_out,
            "world_settings": world_settings,
            "locations": locations,
            "timeline_notes": timeline_notes,
            "style_notes": style_notes,
        }

    def get_by_id(self, bible_id: str) -> Optional[Bible]:
        """同步读取 `by_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_id` 这一入口。
        关键输入:
        - bible_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[Bible]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one("SELECT * FROM bibles WHERE id = ?", (bible_id,))
        if not row:
            return None
        data = self._to_mapper_dict(row["id"], row["novel_id"])
        try:
            return BibleMapper.from_dict(data)
        except ValueError as e:
            logger.warning("Bible %s invalid: %s", bible_id, e)
            return None

    def get_by_novel_id(self, novel_id: NovelId) -> Optional[Bible]:
        """同步读取 `by_novel_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_novel_id` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[Bible]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one(
            "SELECT * FROM bibles WHERE novel_id = ?", (novel_id.value,)
        )
        if not row:
            return None
        data = self._to_mapper_dict(row["id"], row["novel_id"])
        try:
            return BibleMapper.from_dict(data)
        except ValueError as e:
            logger.warning("Bible for novel %s invalid: %s", novel_id.value, e)
            return None

    def delete(self, bible_id: str) -> None:
        """同步执行 `delete` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `delete` 这一入口。
        关键输入:
        - bible_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one("SELECT novel_id FROM bibles WHERE id = ?", (bible_id,))
        if not row:
            return
        novel_id = row["novel_id"]
        conn = self._conn()
        try:
            self._clear_children(conn, novel_id)
            conn.execute("DELETE FROM bibles WHERE id = ?", (bible_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def exists(self, bible_id: str) -> bool:
        """同步执行 `exists` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `exists` 这一入口。
        关键输入:
        - bible_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 布尔值，表示判断、校验或执行条件是否成立。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        r = self.db.fetch_one("SELECT 1 AS o FROM bibles WHERE id = ?", (bible_id,))
        return r is not None

    def update_character_anchors(
        self,
        novel_id: str,
        character_id: str,
        *,
        mental_state: str,
        verbal_tic: str,
        idle_behavior: str,
    ) -> None:
        """仅更新 bible_characters 声线锚点列（不落整本 Bible）。"""
        row = self.db.fetch_one(
            "SELECT id FROM bible_characters WHERE novel_id = ? AND id = ?",
            (novel_id, character_id),
        )
        if not row:
            from domain.shared.exceptions import EntityNotFoundError

            raise EntityNotFoundError("Character", f"{novel_id}/{character_id}")
        now = self._now()
        self.db.execute(
            """
            UPDATE bible_characters
            SET mental_state = ?, verbal_tic = ?, idle_behavior = ?, updated_at = ?
            WHERE novel_id = ? AND id = ?
            """,
            (mental_state, verbal_tic, idle_behavior, now, novel_id, character_id),
        )
        self.db.get_connection().commit()
