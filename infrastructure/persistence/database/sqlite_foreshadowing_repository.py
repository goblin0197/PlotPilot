"""SQLite 伏笔与潜台词账本仓储。

以单行 JSON 快照持久化 ForeshadowingRegistry（与 ForeshadowingMapper 一致），
替代文件系统 foreshadowings/{novel_id}.json。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from domain.novel.entities.foreshadowing_registry import ForeshadowingRegistry
from domain.novel.repositories.foreshadowing_repository import ForeshadowingRepository
from domain.novel.value_objects.novel_id import NovelId
from infrastructure.persistence.database.connection import DatabaseConnection
from infrastructure.persistence.mappers.foreshadowing_mapper import ForeshadowingMapper

logger = logging.getLogger(__name__)


class SqliteForeshadowingRepository(ForeshadowingRepository):
    """伏笔注册表 SQLite 实现。"""

    def __init__(self, db: DatabaseConnection):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - db: 数据库连接或访问封装，用于执行持久化操作。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self._db = db

    def get_by_novel_id(self, novel_id: NovelId) -> Optional[ForeshadowingRegistry]:
        """同步读取 `by_novel_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_novel_id` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[ForeshadowingRegistry]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        exists = self._db.fetch_one(
            "SELECT 1 AS o FROM novels WHERE id = ?",
            (novel_id.value,),
        )
        if not exists:
            return None

        row = self._db.fetch_one(
            "SELECT payload FROM novel_foreshadow_registry WHERE novel_id = ?",
            (novel_id.value,),
        )
        if not row:
            return ForeshadowingRegistry(
                id=f"fr-{novel_id.value}",
                novel_id=novel_id,
            )

        try:
            data = json.loads(row["payload"])
            return ForeshadowingMapper.from_dict(data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                "Invalid foreshadow registry JSON for novel %s: %s",
                novel_id.value,
                e,
            )
            return ForeshadowingRegistry(
                id=f"fr-{novel_id.value}",
                novel_id=novel_id,
            )

    def save(self, registry: ForeshadowingRegistry) -> None:
        """同步执行 `save` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `save` 这一入口。
        关键输入:
        - registry: `ForeshadowingRegistry` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        novel_row = self._db.fetch_one(
            "SELECT 1 AS o FROM novels WHERE id = ?",
            (registry.novel_id.value,),
        )
        if not novel_row:
            raise ValueError(f"Novel {registry.novel_id.value} does not exist")

        payload = json.dumps(
            ForeshadowingMapper.to_dict(registry),
            ensure_ascii=False,
        )
        now = datetime.utcnow().isoformat()
        sql = """
            INSERT INTO novel_foreshadow_registry (novel_id, payload, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(novel_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = excluded.updated_at
        """
        self._db.execute(sql, (registry.novel_id.value, payload, now))
        self._db.get_connection().commit()

    def delete(self, novel_id: NovelId) -> None:
        """同步执行 `delete` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `delete` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        self._db.execute(
            "DELETE FROM novel_foreshadow_registry WHERE novel_id = ?",
            (novel_id.value,),
        )
        self._db.get_connection().commit()
