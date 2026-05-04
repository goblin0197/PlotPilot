"""新书向导 / Bible 异步生成：向 UI 暴露最近一次失败原因（内存态，单进程有效）。"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_lock = threading.Lock()
_by_novel: Dict[str, Dict[str, Any]] = {}


def clear_bible_generation_state(novel_id: str) -> None:
    """同步写入、更新或清理 `bible_generation_state` 相关状态。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `clear_bible_generation_state` 这一入口。
    关键输入:
    - novel_id: 业务标识或配置键，用于定位目标记录。
    关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    with _lock:
        _by_novel.pop(novel_id, None)


def record_bible_generation_failure(novel_id: str, stage: str, message: str) -> None:
    """同步执行 `record_bible_generation_failure` 对应的业务步骤。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `record_bible_generation_failure` 这一入口。
    关键输入:
    - novel_id: 业务标识或配置键，用于定位目标记录。
    - stage: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
    - message: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
    关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    text = (message or "").strip()
    if len(text) > 4000:
        text = text[:4000] + "…"
    with _lock:
        _by_novel[novel_id] = {
            "error": text,
            "stage": (stage or "").strip() or "unknown",
            "at": datetime.now(timezone.utc).isoformat(),
        }


def get_bible_generation_state(novel_id: str) -> Optional[Dict[str, Any]]:
    """同步读取 `bible_generation_state` 相关的数据或状态。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `get_bible_generation_state` 这一入口。
    关键输入:
    - novel_id: 业务标识或配置键，用于定位目标记录。
    关键输出: `Optional[Dict[str, Any]]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    with _lock:
        row = _by_novel.get(novel_id)
        return dict(row) if row else None
