"""
三元组仓储 — 与 schema.sql 中 triples + 子表对齐，经 SqliteKnowledgeRepository 写入。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Mapping, Optional, Union

from domain.bible.triple import Triple, SourceType
from domain.knowledge.triple_provenance import TripleProvenanceRecord
from infrastructure.persistence.database.connection import DatabaseConnection
from infrastructure.persistence.database.sqlite_knowledge_repository import SqliteKnowledgeRepository


def _persist_source_type(st: SourceType) -> str:
    """同步执行 `_persist_source_type` 对应的业务步骤。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_persist_source_type` 这一入口。
    关键输入:
    - st: `SourceType` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `str`；具体语义由调用场景和返回类型共同约束。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if st == SourceType.MANUAL:
        return "manual"
    if st == SourceType.AI_GENERATED:
        return "ai_generated"
    if st == SourceType.BIBLE_GENERATED:
        return "bible_generated"
    if st in (SourceType.AUTO_INFERRED, SourceType.CHAPTER_INFERRED):
        return "chapter_inferred"
    return st.value


def _load_source_type(raw: Optional[str]) -> SourceType:
    """同步执行 `_load_source_type` 对应的业务步骤。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_load_source_type` 这一入口。
    关键输入:
    - raw: `Optional[str]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `SourceType`；具体语义由调用场景和返回类型共同约束。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if not raw:
        return SourceType.MANUAL
    if raw == "chapter_inferred":
        return SourceType.CHAPTER_INFERRED
    if raw == "bible_generated":
        return SourceType.BIBLE_GENERATED
    if raw == "auto_inferred":
        return SourceType.AUTO_INFERRED
    try:
        return SourceType(raw)
    except ValueError:
        return SourceType.MANUAL


def _triple_to_fact_dict(triple: Triple) -> dict:
    """同步执行 `_triple_to_fact_dict` 对应的业务步骤。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_triple_to_fact_dict` 这一入口。
    关键输入:
    - triple: `Triple` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `dict`；包含后续流程所需字段的结构化映射。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    chapter_num: Optional[int] = None
    if triple.source_chapter_id:
        sid = str(triple.source_chapter_id)
        if sid.isdigit():
            chapter_num = int(sid)

    related_ints: list[int] = []
    for x in triple.related_chapters or []:
        try:
            related_ints.append(int(x))
        except (TypeError, ValueError):
            pass

    attrs = dict(triple.attributes or {})
    # 展示用名称与列级重要程度/地点类型（由 Bible 等写入 attributes，不落冗余 JSON）
    subject_label = attrs.pop("subject_label", None)
    object_label = attrs.pop("object_label", None)
    subject_importance = attrs.pop("subject_importance", None)
    subject_location_type = attrs.pop("subject_location_type", None)
    # object_importance / object_location_type 保留在 attributes 供前端补全客体节点

    if triple.subject_type != triple.object_type:
        attrs["object_type"] = triple.object_type
    if triple.source_chapter_id and not str(triple.source_chapter_id).isdigit():
        attrs["source_story_node_id"] = str(triple.source_chapter_id)
    non_numeric = [str(x) for x in (triple.related_chapters or []) if not str(x).isdigit()]
    if non_numeric:
        attrs["related_story_nodes"] = ",".join(non_numeric)

    first_app: Optional[int] = None
    fa = triple.first_appearance
    if isinstance(fa, int):
        first_app = fa
    elif isinstance(fa, str) and fa.strip().isdigit():
        first_app = int(fa.strip())

    subj_text = (subject_label or triple.subject_id or "").strip() or triple.subject_id
    obj_text = (object_label or triple.object_id or "").strip() or triple.object_id

    return {
        "id": triple.id,
        "subject": subj_text,
        "predicate": triple.predicate,
        "object": obj_text,
        "chapter_id": chapter_num,
        "note": "",
        "entity_type": triple.subject_type,
        "importance": subject_importance,
        "location_type": subject_location_type,
        "description": triple.description,
        "first_appearance": first_app,
        "related_chapters": related_ints,
        "tags": list(triple.tags or []),
        "attributes": attrs,
        "confidence": triple.confidence,
        "source_type": _persist_source_type(triple.source_type),
        "subject_entity_id": triple.subject_id,
        "object_entity_id": triple.object_id,
    }


BIBLE_LOCATION_ATTR_KEY = "bible_location_id"
CONTAINMENT_PREDICATE = "位于"
BIBLE_ANCHOR_PREDICATE = "地图地点"


class TripleRepository:
    """三元组仓储（与 Knowledge 层共用 triples 表形状）

    生产环境应传入共享的 ``get_database()`` 实例，避免每次 ``DatabaseConnection(path)``
    重复跑 schema 与刷屏「Database initialized」。
    测试可传入 ``str`` 路径或 ``DatabaseConnection``。
    """

    def __init__(self, db: Union[DatabaseConnection, str, None] = None):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - db: 数据库连接或访问封装，用于执行持久化操作。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if isinstance(db, DatabaseConnection):
            self._db = db
        elif isinstance(db, str):
            self._db = DatabaseConnection(db)
        else:
            from infrastructure.persistence.database.connection import get_database

            self._db = get_database()
        self.db_path = self._db.db_path
        self._kr = SqliteKnowledgeRepository(self._db)

    def persist_triple_sync(self, novel_id: str, triple: Triple) -> None:
        """同步写入三元组（供 Bible 地点同步等非 async 调用链使用）。"""
        self._kr.save_triple(novel_id, _triple_to_fact_dict(triple))

    def delete_triple_sync(self, triple_id: str) -> bool:
        """同步写入、更新或清理 `triple_sync` 相关状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `delete_triple_sync` 这一入口。
        关键输入:
        - triple_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 布尔值，表示判断、校验或执行条件是否成立。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        cur = self._db.execute("DELETE FROM triples WHERE id = ?", (triple_id,))
        self._db.get_connection().commit()
        return cur.rowcount > 0

    def get_by_novel_sync(self, novel_id: str) -> List[Triple]:
        """同步：获取小说所有三元组。"""
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        rows = self._db.fetch_all(
            "SELECT * FROM triples WHERE novel_id = ? ORDER BY created_at DESC",
            (novel_id,),
        )
        return [self._row_to_triple(r, more, tags, attrs) for r in rows]

    def get_by_entity_ids_sync(self, novel_id: str, entity_ids: List[str]) -> List[Triple]:
        """同步：按实体名称列表召回关联三元组（subject 或 object 命中）。"""
        if not entity_ids:
            return []
        placeholders = ",".join("?" * len(entity_ids))
        rows = self._db.fetch_all(
            f"""
            SELECT * FROM triples
            WHERE novel_id = ?
              AND (
                COALESCE(subject_entity_id, subject) IN ({placeholders})
                OR COALESCE(object_entity_id, object) IN ({placeholders})
              )
            ORDER BY confidence DESC, created_at DESC
            """,
            (novel_id, *entity_ids, *entity_ids),
        )
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        return [self._row_to_triple(r, more, tags, attrs) for r in rows]

    def search_by_predicate_sync(
        self,
        novel_id: str,
        predicates: List[str],
        subject_ids: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Triple]:
        """同步：按谓词列表（可选 subject 过滤）召回三元组。"""
        if not predicates:
            return []
        pred_placeholders = ",".join("?" * len(predicates))
        params: list = [novel_id, *predicates]
        subj_clause = ""
        if subject_ids:
            s_placeholders = ",".join("?" * len(subject_ids))
            subj_clause = f"AND COALESCE(subject_entity_id, subject) IN ({s_placeholders})"
            params.extend(subject_ids)
        params.append(limit)
        rows = self._db.fetch_all(
            f"""
            SELECT * FROM triples
            WHERE novel_id = ?
              AND predicate IN ({pred_placeholders})
              {subj_clause}
            ORDER BY confidence DESC, created_at DESC
            LIMIT ?
            """,
            tuple(params),
        )
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        return [self._row_to_triple(r, more, tags, attrs) for r in rows]

    def get_recent_triples_sync(
        self,
        novel_id: str,
        chapter_number: int,
        chapter_range: int = 5,
        limit: int = 20,
    ) -> List[Triple]:
        """同步：获取最近 chapter_range 章内的三元组。"""
        min_chapter = max(1, chapter_number - chapter_range)
        rows = self._db.fetch_all(
            """
            SELECT * FROM triples
            WHERE novel_id = ?
              AND chapter_number IS NOT NULL
              AND CAST(chapter_number AS INTEGER) >= ?
              AND CAST(chapter_number AS INTEGER) <= ?
            ORDER BY chapter_number DESC, created_at DESC
            LIMIT ?
            """,
            (novel_id, min_chapter, chapter_number, limit),
        )
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        return [self._row_to_triple(r, more, tags, attrs) for r in rows]

    def get_containment_meta_by_bible_location_id(
        self, novel_id: str, bible_location_id: str
    ) -> Optional[dict]:
        """同步读取 `containment_meta_by_bible_location_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_containment_meta_by_bible_location_id` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - bible_location_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[dict]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self._db.fetch_one(
            """
            SELECT t.id, t.source_type
            FROM triples t
            INNER JOIN triple_attr a ON a.triple_id = t.id AND a.attr_key = ?
            WHERE t.novel_id = ? AND t.predicate = ? AND a.attr_value = ?
            LIMIT 1
            """,
            (BIBLE_LOCATION_ATTR_KEY, novel_id, CONTAINMENT_PREDICATE, bible_location_id),
        )
        return dict(row) if row else None

    def list_bible_generated_containment_with_location_ids(
        self, novel_id: str,
    ) -> List[dict]:
        """同步读取 `bible_generated_containment_with_location_ids` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `list_bible_generated_containment_with_location_ids` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[dict]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self._db.fetch_all(
            """
            SELECT DISTINCT t.id, a.attr_value AS bible_location_id
            FROM triples t
            INNER JOIN triple_attr a ON a.triple_id = t.id AND a.attr_key = ?
            WHERE t.novel_id = ? AND t.predicate = ? AND t.source_type = 'bible_generated'
            """,
            (BIBLE_LOCATION_ATTR_KEY, novel_id, CONTAINMENT_PREDICATE),
        )
        return [dict(r) for r in rows]

    def list_bible_generated_anchor_with_location_ids(
        self, novel_id: str,
    ) -> List[dict]:
        """同步读取 `bible_generated_anchor_with_location_ids` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `list_bible_generated_anchor_with_location_ids` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[dict]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self._db.fetch_all(
            """
            SELECT DISTINCT t.id, a.attr_value AS bible_location_id
            FROM triples t
            INNER JOIN triple_attr a ON a.triple_id = t.id AND a.attr_key = ?
            WHERE t.novel_id = ? AND t.predicate = ? AND t.source_type = 'bible_generated'
            """,
            (BIBLE_LOCATION_ATTR_KEY, novel_id, BIBLE_ANCHOR_PREDICATE),
        )
        return [dict(r) for r in rows]

    def _row_to_triple(
        self,
        row: Mapping[str, Any],
        more: dict[str, list[int]],
        tags: dict[str, list[str]],
        attrs: dict[str, dict[str, str]],
    ) -> Triple:
        """同步转换或规范化 `row_triple` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_row_to_triple` 这一入口。
        关键输入:
        - row: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        - more: `dict[str, list[int]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        - tags: `dict[str, list[str]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        - attrs: `dict[str, dict[str, str]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Triple`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        tid = row["id"]
        merged = dict(attrs.get(tid, {}))
        source_story_node_id = merged.pop("source_story_node_id", None)
        related_nodes_raw = merged.pop("related_story_nodes", None)
        object_type_stored = merged.pop("object_type", None)
        extra_related: list[str] = []
        if related_nodes_raw:
            extra_related = [s.strip() for s in str(related_nodes_raw).split(",") if s.strip()]

        related_chapters: list[str] = [str(n) for n in more.get(tid, [])]
        related_chapters.extend(extra_related)

        ch_num = row["chapter_number"]
        source_chapter_id: Optional[str] = None
        if source_story_node_id:
            source_chapter_id = str(source_story_node_id)
        elif ch_num is not None:
            source_chapter_id = str(int(ch_num))

        fa = row["first_appearance"]
        first_appearance: Optional[str] = str(fa) if fa is not None else None

        created = row["created_at"]
        updated = row["updated_at"]
        subject_type = row["entity_type"] or "character"
        object_type = object_type_stored or subject_type

        return Triple(
            id=row["id"],
            novel_id=row["novel_id"],
            subject_type=subject_type,
            subject_id=row["subject_entity_id"] or row["subject"],
            predicate=row["predicate"],
            object_type=object_type,
            object_id=row["object_entity_id"] or row["object"],
            confidence=float(row["confidence"]) if row["confidence"] is not None else 1.0,
            source_type=_load_source_type(row["source_type"]),
            source_chapter_id=source_chapter_id,
            first_appearance=first_appearance,
            related_chapters=related_chapters,
            description=row["description"],
            tags=list(tags.get(tid, [])),
            attributes=merged,
            created_at=datetime.fromisoformat(created) if isinstance(created, str) else datetime.now(),
            updated_at=datetime.fromisoformat(updated) if isinstance(updated, str) else datetime.now(),
        )

    async def save(self, triple: Triple) -> Triple:
        """异步执行 `save` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `save` 这一入口。
        关键输入:
        - triple: `Triple` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Triple`；具体语义由调用场景和返回类型共同约束。
        副作用: 会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self._kr.save_triple(triple.novel_id, _triple_to_fact_dict(triple))
        return triple

    async def save_with_provenance(
        self, triple: Triple, records: List[TripleProvenanceRecord]
    ) -> Triple:
        """异步写入、更新或清理 `with_provenance` 相关状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `save_with_provenance` 这一入口。
        关键输入:
        - triple: `Triple` 类型的业务输入，参与本函数的主要计算或流程控制。
        - records: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: `Triple`；具体语义由调用场景和返回类型共同约束。
        副作用: 会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        rows = [
            p.to_row_dict(triple.novel_id, triple.id, f"tp-{uuid.uuid4().hex}")
            for p in records
        ]
        self._kr.save_triple(
            triple.novel_id,
            _triple_to_fact_dict(triple),
            provenance_rows=rows,
            provenance_mode="replace",
        )
        return triple

    async def append_provenance_for_triple(
        self, triple: Triple, records: List[TripleProvenanceRecord]
    ) -> None:
        """异步执行 `append_provenance_for_triple` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `append_provenance_for_triple` 这一入口。
        关键输入:
        - triple: `Triple` 类型的业务输入，参与本函数的主要计算或流程控制。
        - records: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        rows = [
            p.to_row_dict(triple.novel_id, triple.id, f"tp-{uuid.uuid4().hex}")
            for p in records
        ]
        self._kr.append_triple_provenance_only(triple.novel_id, triple.id, rows)

    async def update(self, triple: Triple) -> Triple:
        """异步执行 `update` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `update` 这一入口。
        关键输入:
        - triple: `Triple` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Triple`；具体语义由调用场景和返回类型共同约束。
        副作用: 会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        triple.updated_at = datetime.now()
        self._kr.save_triple(triple.novel_id, _triple_to_fact_dict(triple))
        return triple

    async def save_batch(self, triples: List[Triple]) -> List[Triple]:
        """异步写入、更新或清理 `batch` 相关状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `save_batch` 这一入口。
        关键输入:
        - triples: `List[Triple]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `List[Triple]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        for t in triples:
            await self.save(t)
        return triples

    async def get_by_id(self, triple_id: str) -> Optional[Triple]:
        """异步读取 `by_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_id` 这一入口。
        关键输入:
        - triple_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[Triple]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self._db.fetch_one("SELECT * FROM triples WHERE id = ?", (triple_id,))
        if not row:
            return None
        novel_id = row["novel_id"]
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        return self._row_to_triple(row, more, tags, attrs)

    async def get_by_novel(self, novel_id: str) -> List[Triple]:
        """异步读取 `by_novel` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_novel` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[Triple]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        rows = self._db.fetch_all(
            "SELECT * FROM triples WHERE novel_id = ? ORDER BY created_at DESC",
            (novel_id,),
        )
        return [self._row_to_triple(r, more, tags, attrs) for r in rows]

    async def find_by_relation(
        self,
        novel_id: str,
        subject_type: str,
        subject_id: str,
        predicate: str,
        object_type: str,
        object_id: str,
    ) -> Optional[Triple]:
        """异步读取 `by_relation` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `find_by_relation` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - subject_type: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - subject_id: 业务标识或配置键，用于定位目标记录。
        - predicate: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - object_type: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - object_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[Triple]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self._db.fetch_one(
            """
            SELECT * FROM triples
            WHERE novel_id = ?
              AND predicate = ?
              AND COALESCE(subject_entity_id, subject) = ?
              AND COALESCE(object_entity_id, object) = ?
            """,
            (novel_id, predicate, subject_id, object_id),
        )
        if not row:
            return None
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        t = self._row_to_triple(row, more, tags, attrs)
        if t.subject_type != subject_type or t.object_type != object_type:
            return None
        return t

    async def get_by_source_type(
        self,
        novel_id: str,
        source_type: SourceType,
        min_confidence: float = 0.0,
    ) -> List[Triple]:
        """异步读取 `by_source_type` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_source_type` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - source_type: `SourceType` 类型的业务输入，参与本函数的主要计算或流程控制。
        - min_confidence: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `List[Triple]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        persisted = _persist_source_type(source_type)
        rows = self._db.fetch_all(
            """
            SELECT * FROM triples
            WHERE novel_id = ?
              AND source_type = ?
              AND COALESCE(confidence, 0) >= ?
            ORDER BY confidence DESC, created_at DESC
            """,
            (novel_id, persisted, min_confidence),
        )
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        return [self._row_to_triple(r, more, tags, attrs) for r in rows]

    async def get_by_chapter(self, chapter_id: str) -> List[Triple]:
        """异步读取 `by_chapter` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_chapter` 这一入口。
        关键输入:
        - chapter_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[Triple]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self._db.fetch_all(
            """
            SELECT DISTINCT t.* FROM triples t
            LEFT JOIN triple_attr a
              ON a.triple_id = t.id AND a.attr_key = 'source_story_node_id'
            WHERE a.attr_value = ?
               OR CAST(t.chapter_number AS TEXT) = ?
            ORDER BY t.created_at DESC
            """,
            (chapter_id, chapter_id),
        )
        if not rows:
            return []
        novel_ids = {r["novel_id"] for r in rows}
        out: List[Triple] = []
        for nid in novel_ids:
            more, tags, attrs = self._kr.get_triple_side_data_for_novel(nid)
            for r in rows:
                if r["novel_id"] == nid:
                    out.append(self._row_to_triple(r, more, tags, attrs))
        return out

    async def get_by_subject(
        self,
        novel_id: str,
        subject_type: str,
        subject_id: str,
    ) -> List[Triple]:
        """异步读取 `by_subject` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_subject` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - subject_type: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - subject_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[Triple]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self._db.fetch_all(
            """
            SELECT * FROM triples
            WHERE novel_id = ?
              AND COALESCE(subject_entity_id, subject) = ?
            ORDER BY created_at DESC
            """,
            (novel_id, subject_id),
        )
        if not novel_id:
            return []
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        out: List[Triple] = []
        for row in rows:
            t = self._row_to_triple(row, more, tags, attrs)
            if t.subject_type == subject_type:
                out.append(t)
        return out

    async def get_by_object(
        self,
        novel_id: str,
        object_type: str,
        object_id: str,
    ) -> List[Triple]:
        """异步读取 `by_object` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_object` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - object_type: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - object_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `List[Triple]`；按调用约定排序或过滤后的结果集合。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        rows = self._db.fetch_all(
            """
            SELECT * FROM triples
            WHERE novel_id = ?
              AND COALESCE(object_entity_id, object) = ?
            ORDER BY created_at DESC
            """,
            (novel_id, object_id),
        )
        if not novel_id:
            return []
        more, tags, attrs = self._kr.get_triple_side_data_for_novel(novel_id)
        out: List[Triple] = []
        for row in rows:
            t = self._row_to_triple(row, more, tags, attrs)
            if t.object_type == object_type:
                out.append(t)
        return out

    async def delete(self, triple_id: str) -> bool:
        """异步执行 `delete` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `delete` 这一入口。
        关键输入:
        - triple_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 布尔值，表示判断、校验或执行条件是否成立。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        cur = self._db.execute("DELETE FROM triples WHERE id = ?", (triple_id,))
        self._db.get_connection().commit()
        return cur.rowcount > 0

    async def delete_by_novel(self, novel_id: str) -> int:
        """异步写入、更新或清理 `by_novel` 相关状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `delete_by_novel` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `int`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能读取或写入 SQLite/仓储状态；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        cur = self._db.execute("DELETE FROM triples WHERE novel_id = ?", (novel_id,))
        self._db.get_connection().commit()
        return cur.rowcount
