"""ForeshadowingRegistry 数据映射器"""
from typing import Dict, Any
from datetime import datetime
from domain.novel.entities.foreshadowing_registry import ForeshadowingRegistry
from domain.novel.entities.subtext_ledger_entry import SubtextLedgerEntry
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.foreshadowing import (
    Foreshadowing,
    ForeshadowingStatus,
    ImportanceLevel,
)


class ForeshadowingMapper:
    """ForeshadowingRegistry 实体与字典数据之间的映射器"""

    @staticmethod
    def _to_int(value: Any, field_name: str) -> int:
        """同步执行 `_to_int` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_to_int` 这一入口。
        关键输入:
        - value: 待校验、转换或写入的值，类型约束为 `Any`。
        - field_name: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `int`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be an integer")
        try:
            return int(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"{field_name} must be an integer, got {value!r}") from e

    @staticmethod
    def _to_optional_int(value: Any, field_name: str) -> Any:
        """同步执行 `_to_optional_int` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_to_optional_int` 这一入口。
        关键输入:
        - value: 待校验、转换或写入的值，类型约束为 `Any`。
        - field_name: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Any`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if value in (None, ""):
            return None
        return ForeshadowingMapper._to_int(value, field_name)

    @staticmethod
    def to_dict(registry: ForeshadowingRegistry) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入:
        - registry: `ForeshadowingRegistry` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "id": registry.id,
            "novel_id": registry.novel_id.value,
            "foreshadowings": [
                {
                    "id": f.id,
                    "planted_in_chapter": f.planted_in_chapter,
                    "description": f.description,
                    "importance": f.importance.value,
                    "status": f.status.value,
                    "suggested_resolve_chapter": f.suggested_resolve_chapter,
                    "resolved_in_chapter": f.resolved_in_chapter,
                }
                for f in registry.foreshadowings
            ],
            "subtext_entries": [
                {
                    "id": e.id,
                    "chapter": e.chapter,
                    "character_id": e.character_id,
                    "question": e.question,
                    "status": e.status,
                    "consumed_at_chapter": e.consumed_at_chapter,
                    "created_at": e.created_at.isoformat(),
                    "suggested_resolve_chapter": getattr(e, "suggested_resolve_chapter", None),
                    "resolve_chapter_window": getattr(e, "resolve_chapter_window", None),
                    "importance": getattr(e, "importance", "medium"),
                }
                for e in registry.subtext_entries
            ],
        }

    @staticmethod
    def _subtext_question_from_row(e_data: Dict[str, Any]) -> str:
        """兼容旧 JSON：hidden_clue / question。"""
        q = e_data.get("question")
        if q is not None and str(q).strip():
            return str(q).strip()
        legacy = e_data.get("hidden_clue")
        if legacy is not None:
            return str(legacy).strip()
        return ""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ForeshadowingRegistry:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `from_dict` 这一入口。
        关键输入:
        - data: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: `ForeshadowingRegistry`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        required_fields = ["id", "novel_id", "foreshadowings"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        try:
            registry = ForeshadowingRegistry(
                id=data["id"],
                novel_id=NovelId(data["novel_id"]),
            )

            for f_data in data["foreshadowings"]:
                foreshadowing = Foreshadowing(
                    id=f_data["id"],
                    planted_in_chapter=ForeshadowingMapper._to_int(
                        f_data["planted_in_chapter"], "planted_in_chapter"
                    ),
                    description=f_data["description"],
                    importance=ImportanceLevel(f_data["importance"]),
                    status=ForeshadowingStatus(f_data["status"]),
                    suggested_resolve_chapter=ForeshadowingMapper._to_optional_int(
                        f_data.get("suggested_resolve_chapter"), "suggested_resolve_chapter"
                    ),
                    resolved_in_chapter=ForeshadowingMapper._to_optional_int(
                        f_data.get("resolved_in_chapter"), "resolved_in_chapter"
                    ),
                )
                registry.register(foreshadowing)

            if "subtext_entries" in data:
                for e_data in data["subtext_entries"]:
                    entry = SubtextLedgerEntry(
                        id=e_data["id"],
                        chapter=ForeshadowingMapper._to_int(e_data["chapter"], "chapter"),
                        character_id=e_data["character_id"],
                        question=ForeshadowingMapper._subtext_question_from_row(e_data),
                        status=e_data["status"],
                        consumed_at_chapter=ForeshadowingMapper._to_optional_int(
                            e_data.get("consumed_at_chapter"), "consumed_at_chapter"
                        ),
                        suggested_resolve_chapter=ForeshadowingMapper._to_optional_int(
                            e_data.get("suggested_resolve_chapter"), "suggested_resolve_chapter"
                        ),
                        resolve_chapter_window=ForeshadowingMapper._to_optional_int(
                            e_data.get("resolve_chapter_window"), "resolve_chapter_window"
                        ),
                        importance=e_data.get("importance", "medium"),
                        created_at=datetime.fromisoformat(e_data["created_at"]),
                    )
                    registry.add_subtext_entry(entry)

            return registry
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid foreshadowing registry data format: {str(e)}") from e
