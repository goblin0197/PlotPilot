"""SQLite Chapter Review Repository：章节审阅（审定）记录。"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from application.audit.dtos.chapter_review_dto import ChapterReviewDTO
from infrastructure.persistence.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SqliteChapterReviewRepository:
    """chapter_reviews 表读写。"""

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

    def get(self, novel_id: str, chapter_number: int) -> Optional[ChapterReviewDTO]:
        """同步执行 `get` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - chapter_number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Optional[ChapterReviewDTO]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one(
            "SELECT status, memo, created_at, updated_at FROM chapter_reviews WHERE novel_id = ? AND chapter_number = ?",
            (novel_id, int(chapter_number)),
        )
        if not row:
            return None
        # sqlite3.Row behaves like dict in this codebase
        created_at = row.get("created_at")
        updated_at = row.get("updated_at")
        try:
            ca = datetime.fromisoformat(created_at) if isinstance(created_at, str) else datetime.utcnow()
        except Exception:
            ca = datetime.utcnow()
        try:
            ua = datetime.fromisoformat(updated_at) if isinstance(updated_at, str) else ca
        except Exception:
            ua = ca
        return ChapterReviewDTO(
            status=row.get("status", "draft"),
            memo=row.get("memo", "") or "",
            created_at=ca,
            updated_at=ua,
        )

    def upsert(self, novel_id: str, chapter_number: int, *, status: str, memo: str) -> ChapterReviewDTO:
        """同步执行 `upsert` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `upsert` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - chapter_number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - status: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - memo: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `ChapterReviewDTO`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        now = datetime.utcnow().isoformat()
        self.db.execute(
            """
            INSERT INTO chapter_reviews (novel_id, chapter_number, status, memo, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(novel_id, chapter_number) DO UPDATE SET
                status = excluded.status,
                memo = excluded.memo,
                updated_at = excluded.updated_at
            """,
            (novel_id, int(chapter_number), status, memo or "", now, now),
        )
        self.db.get_connection().commit()
        return self.get(novel_id, chapter_number) or ChapterReviewDTO(
            status=status,
            memo=memo or "",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

