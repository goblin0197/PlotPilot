"""EmbeddingConfigService — 嵌入模型配置管理服务（数据库驱动）。

将嵌入模型配置持久化到 SQLite embedding_config 表；
默认模型 ID / 本地路径由环境变量或用户在设置中填写，不在代码中写死。
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EmbeddingConfigModel(BaseModel):
    """嵌入配置数据模型。"""
    model_config = {"protected_namespaces": ()}
    id: str = "default"
    mode: str = "openai"  # local | openai（默认云端，轻量）
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    use_gpu: bool = True
    model_path: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "mode": self.mode,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "use_gpu": self.use_gpu,
            "model_path": self.model_path,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "EmbeddingConfigModel":
        """同步转换或规范化 `row` 相关的数据结构。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `from_row` 这一入口。
        关键输入:
        - row: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: `'EmbeddingConfigModel'`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return cls(
            id=row["id"],
            mode=row.get("mode", "openai"),
            api_key=row.get("api_key", ""),
            base_url=row.get("base_url", ""),
            model=row.get("model", ""),
            use_gpu=bool(row.get("use_gpu", 1)),
            model_path=row.get("model_path", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )


class EmbeddingConfigService:
    """嵌入模型配置服务 — 数据库 CRUD。

    设计决策：
    - 单行配置（id='default'），全局唯一
    - 首次读取时自动插入默认行
    - 所有写操作更新 updated_at
    """

    _DEFAULTS = {
        "id": "default",
        "mode": "openai",
        "api_key": "",
        "base_url": "",
        "model": (os.getenv("EMBEDDING_MODEL") or "").strip(),
        "use_gpu": 1,
        "model_path": (os.getenv("LOCAL_EMBEDDING_MODEL_PATH") or "").strip(),
    }

    def __init__(self, db_connection=None):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - db_connection: 业务输入参数，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self._db = db_connection

    def _get_db(self):
        """获取数据库连接（延迟导入避免循环依赖）。"""
        if self._db is not None:
            return self._db
        from infrastructure.persistence.database.connection import get_database

        return get_database()

    def _ensure_row(self) -> None:
        """确保存在默认配置行（幂等）。"""
        db = self._get_db()
        row = db.execute(
            "SELECT id FROM embedding_config WHERE id = ? LIMIT 1",
            ("default",),
        ).fetchone()
        if row:
            return
        now = datetime.now().isoformat()
        db.execute("""
            INSERT OR IGNORE INTO embedding_config
            (id, mode, api_key, base_url, model, use_gpu, model_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "default",
            "openai",
            "",
            "",
            (os.getenv("EMBEDDING_MODEL") or "").strip(),
            1,
            (os.getenv("LOCAL_EMBEDDING_MODEL_PATH") or "").strip(),
            now,
            now,
        ))
        db.get_connection().commit()
        logger.info("EmbeddingConfigService: 已初始化默认嵌入配置")

    def get_config(self) -> EmbeddingConfigModel:
        """获取当前嵌入配置。"""
        self._ensure_row()
        db = self._get_db()
        row = db.execute(
            "SELECT * FROM embedding_config WHERE id = ? LIMIT 1",
            ("default",),
        ).fetchone()
        if not row:
            # 兜底：返回默认模型
            return EmbeddingConfigModel()
        return EmbeddingConfigModel.from_row(dict(row))

    def update_config(self, **kwargs) -> EmbeddingConfigModel:
        """更新嵌入配置。

        Args:
            **kwargs: 要更新的字段（mode, api_key, base_url, model, use_gpu, model_path）

        Returns:
            更新后的配置
        """
        self._ensure_row()
        db = self._get_db()

        # 构建动态 UPDATE
        allowed = {"mode", "api_key", "base_url", "model", "use_gpu", "model_path"}
        set_clauses = []
        params: list = []
        for key, value in kwargs.items():
            if key not in allowed:
                continue
            if key == "use_gpu":
                value = 1 if value else 0
            set_clauses.append(f"{key} = ?")
            params.append(value)

        if not set_clauses:
            return self.get_config()

        now = datetime.now().isoformat()
        set_clauses.append("updated_at = ?")
        params.append(now)
        params.append("default")  # WHERE id = ?

        sql = f"UPDATE embedding_config SET {', '.join(set_clauses)} WHERE id = ?"
        conn = db.get_connection()
        conn.execute(sql, tuple(params))
        conn.commit()

        logger.info("EmbeddingConfigService: 配置已更新，字段: %s", list(kwargs.keys()))
        return self.get_config()

    def to_api_dict(self) -> Dict[str, Any]:
        """返回 API 友好的字典格式。"""
        cfg = self.get_config()
        result = cfg.to_dict()
        result["created_at"] = cfg.created_at
        result["updated_at"] = cfg.updated_at
        return result


# ── 单例 ──────────────────────────────────────────────

_service_instance: Optional[EmbeddingConfigService] = None


def get_embedding_config_service() -> EmbeddingConfigService:
    """获取全局 EmbeddingConfigService 单例。"""
    global _service_instance
    if _service_instance is None:
        _service_instance = EmbeddingConfigService()
    return _service_instance
