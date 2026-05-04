"""SQLite 章节文风评分仓储"""
from typing import List, Optional
from uuid import uuid4


class SqliteChapterStyleScoreRepository:
    """读写 chapter_style_scores 表。"""

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

    def upsert(
        self,
        novel_id: str,
        chapter_number: int,
        adjective_density: float,
        avg_sentence_length: float,
        sentence_count: int,
        similarity_score: Optional[float],  # None 表示无指纹基准
    ) -> str:
        """同步执行 `upsert` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `upsert` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - chapter_number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - adjective_density: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        - avg_sentence_length: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        - sentence_count: 数量、范围或分页控制参数，用于限制处理规模。
        - similarity_score: `Optional[float]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        existing = self.get_by_chapter(novel_id, chapter_number)
        if existing:
            self.db.execute(
                """
                UPDATE chapter_style_scores
                SET adjective_density = ?,
                    avg_sentence_length = ?,
                    sentence_count = ?,
                    similarity_score = ?,
                    computed_at = CURRENT_TIMESTAMP
                WHERE novel_id = ? AND chapter_number = ?
                """,
                (
                    adjective_density,
                    avg_sentence_length,
                    sentence_count,
                    similarity_score,
                    novel_id,
                    chapter_number,
                ),
            )
            return existing["score_id"]

        score_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO chapter_style_scores
            (score_id, novel_id, chapter_number, adjective_density,
             avg_sentence_length, sentence_count, similarity_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                score_id,
                novel_id,
                chapter_number,
                adjective_density,
                avg_sentence_length,
                sentence_count,
                similarity_score,
            ),
        )
        return score_id

    def get_by_chapter(
        self, novel_id: str, chapter_number: int
    ) -> Optional[dict]:
        """同步读取 `by_chapter` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_chapter` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - chapter_number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Optional[dict]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one(
            """
            SELECT score_id, novel_id, chapter_number, adjective_density,
                   avg_sentence_length, sentence_count, similarity_score, computed_at
            FROM chapter_style_scores
            WHERE novel_id = ? AND chapter_number = ?
            """,
            (novel_id, chapter_number),
        )
        return dict(row) if row else None

    def list_by_novel(
        self, novel_id: str, limit: int = 50
    ) -> List[dict]:
        """同步读取 `by_novel` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `list_by_novel` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - limit: 数量、范围或分页控制参数，用于限制处理规模。
        关键输出: `List[dict]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self.db.fetch_all(
            """
            SELECT score_id, novel_id, chapter_number, adjective_density,
                   avg_sentence_length, sentence_count, similarity_score, computed_at
            FROM chapter_style_scores
            WHERE novel_id = ?
            ORDER BY chapter_number ASC
            LIMIT ?
            """,
            (novel_id, limit),
        )
        return [dict(r) for r in rows]
