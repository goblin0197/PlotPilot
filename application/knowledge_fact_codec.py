"""知识三元组 ↔ 持久化/API 字典（单一形状，避免字段漂移）"""
from __future__ import annotations

from typing import Any, Dict

from domain.knowledge.knowledge_triple import KnowledgeTriple


def dict_to_knowledge_triple(d: Dict[str, Any]) -> KnowledgeTriple:
    """同步执行 `dict_to_knowledge_triple` 对应的业务步骤。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `dict_to_knowledge_triple` 这一入口。
    关键输入:
    - d: `Dict[str, Any]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `KnowledgeTriple`；具体语义由调用场景和返回类型共同约束。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    return KnowledgeTriple(
        id=d["id"],
        subject=d.get("subject", ""),
        predicate=d.get("predicate", ""),
        object=d.get("object", ""),
        chapter_id=d.get("chapter_id"),
        note=d.get("note", "") or "",
        entity_type=d.get("entity_type"),
        importance=d.get("importance"),
        location_type=d.get("location_type"),
        description=d.get("description"),
        first_appearance=d.get("first_appearance"),
        related_chapters=d.get("related_chapters") or [],
        tags=d.get("tags") or [],
        attributes=d.get("attributes") or {},
        confidence=d.get("confidence"),
        source_type=d.get("source_type"),
        subject_entity_id=d.get("subject_entity_id"),
        object_entity_id=d.get("object_entity_id"),
    )


def knowledge_triple_to_dict(f: KnowledgeTriple) -> Dict[str, Any]:
    """同步执行 `knowledge_triple_to_dict` 对应的业务步骤。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `knowledge_triple_to_dict` 这一入口。
    关键输入:
    - f: `KnowledgeTriple` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    return {
        "id": f.id,
        "subject": f.subject,
        "predicate": f.predicate,
        "object": f.object,
        "chapter_id": f.chapter_id,
        "note": f.note,
        "entity_type": f.entity_type,
        "importance": f.importance,
        "location_type": f.location_type,
        "description": f.description,
        "first_appearance": f.first_appearance,
        "related_chapters": list(f.related_chapters),
        "tags": list(f.tags),
        "attributes": dict(f.attributes),
        "confidence": f.confidence,
        "source_type": f.source_type,
        "subject_entity_id": f.subject_entity_id,
        "object_entity_id": f.object_entity_id,
    }
