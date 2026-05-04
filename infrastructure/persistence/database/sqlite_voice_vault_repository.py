"""SQLite Voice Vault Repository Implementation"""
import logging
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from domain.novel.repositories.voice_vault_repository import VoiceVaultRepository
from infrastructure.persistence.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SqliteVoiceVaultRepository(VoiceVaultRepository):
    """SQLite Voice Vault Repository 实现"""

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

    def append_sample(
        self,
        novel_id: str,
        chapter_number: int,
        scene_type: Optional[str],
        ai_original: str,
        author_refined: str,
        diff_analysis: str
    ) -> str:
        """添加文风样本"""
        sample_id = str(uuid4())
        sql = """
            INSERT INTO voice_vault (
                sample_id, novel_id, chapter_number, scene_type,
                ai_original, author_refined, diff_analysis, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()
        self.db.execute(sql, (
            sample_id,
            novel_id,
            chapter_number,
            scene_type,
            ai_original,
            author_refined,
            diff_analysis,
            now
        ))
        self.db.get_connection().commit()
        logger.info(f"Added voice sample: {sample_id} for novel {novel_id}")
        return sample_id

    def list_samples(self, novel_id: str, limit: Optional[int] = None) -> List[dict]:
        """列出小说的文风样本"""
        sql = """
            SELECT sample_id, novel_id, chapter_number, scene_type,
                   ai_original, author_refined, diff_analysis, created_at
            FROM voice_vault
            WHERE novel_id = ?
            ORDER BY created_at DESC
        """
        if limit is not None:
            sql += f" LIMIT {int(limit)}"

        rows = self.db.fetch_all(sql, (novel_id,))
        return [dict(row) for row in rows]

    def get_sample_count(self, novel_id: str) -> int:
        """获取小说的样本数量"""
        sql = "SELECT COUNT(*) as count FROM voice_vault WHERE novel_id = ?"
        row = self.db.fetch_one(sql, (novel_id,))
        return row['count'] if row else 0

    def get_by_novel(
        self, novel_id: str, pov_character_id: Optional[str] = None
    ) -> List[dict]:
        """获取小说的所有样本（用于指纹计算）"""
        # Note: Current schema doesn't have pov_character_id, so we ignore it for now
        sql = """
            SELECT author_refined as content
            FROM voice_vault
            WHERE novel_id = ?
            ORDER BY created_at ASC
        """
        rows = self.db.fetch_all(sql, (novel_id,))
        return [dict(row) for row in rows]
