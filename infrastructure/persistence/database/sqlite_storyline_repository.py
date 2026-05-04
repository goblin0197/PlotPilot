"""SQLite 故事线仓储。"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import List, Optional

from domain.novel.entities.storyline import Storyline
from domain.novel.repositories.storyline_repository import StorylineRepository
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.storyline_milestone import StorylineMilestone
from domain.novel.value_objects.storyline_status import StorylineStatus
from domain.novel.value_objects.storyline_type import StorylineType
from infrastructure.persistence.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def _encode_str_list(items: List[str]) -> str:
    """同步执行 `_encode_str_list` 对应的业务步骤。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_encode_str_list` 这一入口。
    关键输入:
    - items: 结构化数据载荷，通常来自请求、数据库行或上游服务。
    关键输出: `str`；具体语义由调用场景和返回类型共同约束。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    return json.dumps(list(items or []), ensure_ascii=False)


def _decode_str_list(text: str) -> List[str]:
    """同步执行 `_decode_str_list` 对应的业务步骤。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_decode_str_list` 这一入口。
    关键输入:
    - text: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
    关键输出: `List[str]`；按调用约定排序或过滤后的结果集合。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if not text or not text.strip():
        return []
    try:
        data = json.loads(text)
        return list(data) if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


class SqliteStorylineRepository(StorylineRepository):
    """定义 `SqliteStorylineRepository`，作为基础设施层中的仓储协作者。

    职责: 封装数据访问边界，避免上层直接依赖具体持久化细节。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
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

    def save(self, storyline: Storyline) -> None:
        """同步执行 `save` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `save` 这一入口。
        关键输入:
        - storyline: `Storyline` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        now = self._now()
        conn = self._conn()
        try:
            # Check if we need to add new columns
            cursor = conn.execute("PRAGMA table_info(storylines)")
            columns = {row[1] for row in cursor.fetchall()}

            if 'name' not in columns:
                conn.execute("ALTER TABLE storylines ADD COLUMN name TEXT DEFAULT ''")
            if 'description' not in columns:
                conn.execute("ALTER TABLE storylines ADD COLUMN description TEXT DEFAULT ''")
            if 'last_active_chapter' not in columns:
                conn.execute("ALTER TABLE storylines ADD COLUMN last_active_chapter INTEGER DEFAULT 0")
            if 'progress_summary' not in columns:
                conn.execute("ALTER TABLE storylines ADD COLUMN progress_summary TEXT DEFAULT ''")

            conn.execute(
                """
                INSERT INTO storylines (
                    id, novel_id, storyline_type, status,
                    estimated_chapter_start, estimated_chapter_end,
                    current_milestone_index, name, description,
                    last_active_chapter, progress_summary,
                    extensions, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '{}', ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    novel_id = excluded.novel_id,
                    storyline_type = excluded.storyline_type,
                    status = excluded.status,
                    estimated_chapter_start = excluded.estimated_chapter_start,
                    estimated_chapter_end = excluded.estimated_chapter_end,
                    current_milestone_index = excluded.current_milestone_index,
                    name = excluded.name,
                    description = excluded.description,
                    last_active_chapter = excluded.last_active_chapter,
                    progress_summary = excluded.progress_summary,
                    updated_at = excluded.updated_at
                """,
                (
                    storyline.id,
                    storyline.novel_id.value,
                    storyline.storyline_type.value,
                    storyline.status.value,
                    storyline.estimated_chapter_start,
                    storyline.estimated_chapter_end,
                    storyline.current_milestone_index,
                    storyline.name,
                    storyline.description,
                    storyline.last_active_chapter,
                    storyline.progress_summary,
                    now,
                    now,
                ),
            )
            conn.execute(
                "DELETE FROM storyline_milestones WHERE storyline_id = ?",
                (storyline.id,),
            )
            for m in storyline.milestones:
                mid = f"{storyline.id}-m-{m.order}"
                conn.execute(
                    """
                    INSERT INTO storyline_milestones (
                        id, storyline_id, milestone_order, title, description,
                        target_chapter_start, target_chapter_end,
                        prerequisite_list, milestone_triggers
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mid,
                        storyline.id,
                        m.order,
                        m.title,
                        m.description,
                        m.target_chapter_start,
                        m.target_chapter_end,
                        _encode_str_list(m.prerequisites),
                        _encode_str_list(m.triggers),
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def get_by_id(self, storyline_id: str) -> Optional[Storyline]:
        """同步读取 `by_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_id` 这一入口。
        关键输入:
        - storyline_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[Storyline]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one(
            "SELECT * FROM storylines WHERE id = ?", (storyline_id,)
        )
        if not row:
            return None
        return self._row_to_storyline(row)

    def get_by_novel_id(self, novel_id: NovelId) -> List[Storyline]:
        """同步读取 `by_novel_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_novel_id` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[Storyline]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self.db.fetch_all(
            "SELECT * FROM storylines WHERE novel_id = ? ORDER BY id",
            (novel_id.value,),
        )
        return [self._row_to_storyline(r) for r in rows]

    def _milestones(self, storyline_id: str) -> List[StorylineMilestone]:
        """同步执行 `_milestones` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_milestones` 这一入口。
        关键输入:
        - storyline_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[StorylineMilestone]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM storyline_milestones
            WHERE storyline_id = ?
            ORDER BY milestone_order
            """,
            (storyline_id,),
        )
        out: List[StorylineMilestone] = []
        for r in rows:
            out.append(
                StorylineMilestone(
                    order=r["milestone_order"],
                    title=r["title"] or "",
                    description=r["description"] or "",
                    target_chapter_start=r["target_chapter_start"],
                    target_chapter_end=r["target_chapter_end"],
                    prerequisites=_decode_str_list(r["prerequisite_list"] or ""),
                    triggers=_decode_str_list(r["milestone_triggers"] or ""),
                )
            )
        return out

    def _row_to_storyline(self, row: dict) -> Storyline:
        """同步转换或规范化 `row_storyline` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_row_to_storyline` 这一入口。
        关键输入:
        - row: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: `Storyline`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        sid = row["id"]
        milestones = self._milestones(sid)
        return Storyline(
            id=sid,
            novel_id=NovelId(row["novel_id"]),
            storyline_type=StorylineType(row["storyline_type"]),
            status=StorylineStatus(row["status"]),
            estimated_chapter_start=row["estimated_chapter_start"],
            estimated_chapter_end=row["estimated_chapter_end"],
            milestones=milestones,
            current_milestone_index=row["current_milestone_index"],
            name=row.get("name", ""),
            description=row.get("description", ""),
            last_active_chapter=row.get("last_active_chapter", 0),
            progress_summary=row.get("progress_summary", ""),
        )

    def delete(self, storyline_id: str) -> None:
        """同步执行 `delete` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `delete` 这一入口。
        关键输入:
        - storyline_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        conn = self._conn()
        try:
            conn.execute("DELETE FROM storyline_milestones WHERE storyline_id = ?", (storyline_id,))
            conn.execute("DELETE FROM storylines WHERE id = ?", (storyline_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
