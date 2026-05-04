"""在任意 JSON 子树中按「键名约定」改写章号整数，避免为每种快照结构写死解析代码。"""
from __future__ import annotations

from typing import Any, FrozenSet

from domain.novel.value_objects.chapter_renumber_spec import ChapterRenumberSpec

# 默认识别的「整型章号」字段名；新表/新 JSON 只需把键加进集合或通过协调器注入扩展键。
DEFAULT_CHAPTER_INTEGER_JSON_KEYS: FrozenSet[str] = frozenset(
    {
        "chapter_number",
        "chapter",
        "planted_in_chapter",
        "resolved_in_chapter",
        "suggested_resolve_chapter",
        "consumed_at_chapter",
        "first_appearance",
        "target_chapter_start",
        "target_chapter_end",
        "estimated_chapter_start",
        "estimated_chapter_end",
        "current_chapter",
        "last_updated_chapter",
        "resolve_chapter_window",
    }
)


def renumber_chapter_integers_in_json(
    obj: Any,
    spec: ChapterRenumberSpec,
    *,
    keys: FrozenSet[str] = DEFAULT_CHAPTER_INTEGER_JSON_KEYS,
) -> Any:
    """同步执行 `renumber_chapter_integers_in_json` 对应的业务步骤。

    职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `renumber_chapter_integers_in_json` 这一入口。
    关键输入:
    - obj: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
    - spec: `ChapterRenumberSpec` 类型的业务输入，参与本函数的主要计算或流程控制。
    - keys: `FrozenSet[str]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `Any`；具体语义由调用场景和返回类型共同约束。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in keys and isinstance(v, int) and not isinstance(v, bool):
                out[k] = spec.shift_chapter_ref(v)
            else:
                out[k] = renumber_chapter_integers_in_json(v, spec, keys=keys)
        return out
    if isinstance(obj, list):
        return [renumber_chapter_integers_in_json(x, spec, keys=keys) for x in obj]
    if isinstance(obj, tuple):
        return tuple(renumber_chapter_integers_in_json(x, spec, keys=keys) for x in obj)
    return obj
