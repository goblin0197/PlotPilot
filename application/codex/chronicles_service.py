"""双螺旋编年史：按 chapter_index 拉链聚合剧情时间线与语义快照（BFF 聚合，底层表物理隔离）。"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_CHAPTER_IN_TEXT = re.compile(r"第\s*(\d+)\s*章")


def infer_chapter_from_texts(*parts: str) -> Optional[int]:
    """同步执行 `infer_chapter_from_texts` 对应的业务步骤。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `infer_chapter_from_texts` 这一入口。
    关键输入:
    - *parts: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `Optional[int]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    for p in parts:
        if not p:
            continue
        m = _CHAPTER_IN_TEXT.search(p)
        if m:
            return int(m.group(1))
    return None


def anchor_chapter_from_pointers(
    pointer_ids: List[str],
    id_to_number: Dict[str, int],
) -> Optional[int]:
    """同步执行 `anchor_chapter_from_pointers` 对应的业务步骤。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `anchor_chapter_from_pointers` 这一入口。
    关键输入:
    - pointer_ids: `List[str]` 类型的业务输入，参与本函数的主要计算或流程控制。
    - id_to_number: `Dict[str, int]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `Optional[int]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    nums = [id_to_number[i] for i in pointer_ids if i in id_to_number]
    return max(nums) if nums else None


def build_chronicles_rows(
    timeline_notes: List[Tuple[str, str, str, str]],
    snapshots: List[Dict[str, Any]],
    id_to_number: Dict[str, int],
) -> List[Dict[str, Any]]:
    """
    timeline_notes: list of (id, time_point, event, description)
    snapshots: rows with id, name, trigger_type, branch_name, created_at, description, chapter_pointers (list)
    """
    max_num = max(id_to_number.values(), default=1)
    snap_fallback = max_num if max_num >= 1 else 1

    buckets: Dict[int, Dict[str, List]] = {}

    def ensure(ch: int) -> Dict[str, List]:
        """同步执行 `ensure` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `ensure` 这一入口。
        关键输入:
        - ch: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Dict[str, List]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if ch not in buckets:
            buckets[ch] = {"story_events": [], "snapshots": []}
        return buckets[ch]

    for idx, (nid, tp, ev, desc) in enumerate(timeline_notes):
        inferred = infer_chapter_from_texts(tp or "", ev or "", desc or "")
        ch = inferred if inferred is not None else idx + 1
        ch = max(1, ch)
        ensure(ch)["story_events"].append(
            {
                "note_id": nid,
                "time": (tp or "").strip() or "（未标注时间）",
                "title": (ev or "").strip(),
                "description": (desc or "").strip(),
                "source_chapter": inferred,
            }
        )

    for snap in snapshots:
        ptrs = snap.get("chapter_pointers") or []
        if not isinstance(ptrs, list):
            ptrs = []
        anchor = anchor_chapter_from_pointers([str(x) for x in ptrs], id_to_number)
        ch = anchor if anchor is not None else snap_fallback
        ch = max(1, ch)
        ensure(ch)["snapshots"].append(
            {
                "id": snap.get("id"),
                "kind": snap.get("trigger_type") or "AUTO",
                "name": snap.get("name") or "",
                "branch_name": snap.get("branch_name") or "main",
                "created_at": snap.get("created_at"),
                "description": (snap.get("description") or "").strip() or None,
                "anchor_chapter": anchor,
            }
        )

    if not buckets:
        return []

    out: List[Dict[str, Any]] = []
    for ch in sorted(buckets.keys()):
        b = buckets[ch]
        out.append(
            {
                "chapter_index": ch,
                "story_events": b["story_events"],
                "snapshots": b["snapshots"],
            }
        )

    return out
