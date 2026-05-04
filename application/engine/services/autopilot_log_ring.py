"""全托管守护进程日志环：供 SSE 按书目推送真实日志行（非轮询摘要）。

线程安全；与 FileHandler 并存，不向根 logger 重复传播。
"""

from __future__ import annotations

import logging
import re
import threading
import traceback
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple

_NOVEL_ID_IN_BRACKETS = re.compile(r"\[(novel-[a-zA-Z0-9]+)\]")
_NOVEL_ID_LOOSE = re.compile(r"(novel-[a-zA-Z0-9]+)")

_MAX_ENTRIES = 4000

_ring: Deque["AutopilotLogEntry"] = deque(maxlen=_MAX_ENTRIES)
_lock = threading.Lock()
_seq = 0

_handler_installed = False
_handler_lock = threading.Lock()


@dataclass(frozen=True)
class AutopilotLogEntry:
    """定义 `AutopilotLogEntry`，作为应用层中的业务对象。

    职责: 承载本模块的状态、规则或协作入口。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    seq: int
    timestamp_iso: str
    level: str
    message: str
    logger_name: str
    novel_id: Optional[str]


def _extract_novel_id(message: str) -> Optional[str]:
    """同步执行 `_extract_novel_id` 对应的业务步骤。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_extract_novel_id` 这一入口。
    关键输入:
    - message: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
    关键输出: `Optional[str]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if not message:
        return None
    m = _NOVEL_ID_IN_BRACKETS.search(message)
    if m:
        return m.group(1)
    m2 = _NOVEL_ID_LOOSE.search(message)
    if m2:
        return m2.group(1)
    return None


def _matches_novel(entry: AutopilotLogEntry, novel_id: str) -> bool:
    """同步执行 `_matches_novel` 对应的业务步骤。

    职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_matches_novel` 这一入口。
    关键输入:
    - entry: `AutopilotLogEntry` 类型的业务输入，参与本函数的主要计算或流程控制。
    - novel_id: 业务标识或配置键，用于定位目标记录。
    关键输出: 布尔值，表示判断、校验或执行条件是否成立。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if entry.novel_id and entry.novel_id == novel_id:
        return True
    return novel_id in (entry.message or "")


def should_skip_autopilot_log_line(
    level: str,
    message: str,
    logger_name: str = "",
) -> bool:
    """过滤 StreamingBus 等高频 DEBUG，避免 SSE/终端刷屏。"""
    msg = message or ""
    ln = (logger_name or "").lower()
    if "streaming_bus" in ln and (level or "").upper() == "DEBUG":
        return True
    if "[StreamingBus]" in msg and "publish:" in msg:
        return True
    if "[DEBUG]" in msg and "streaming_bus" in msg.lower():
        return True
    if "autopilot_routes" in ln and (level or "").upper() == "DEBUG":
        if "[SSE]" in msg and "chapter" in msg.lower():
            return True
    return False


def should_skip_raw_log_file_line(line: str) -> bool:
    """文件 tail 单行过滤（无独立 logger 字段）。"""
    if "[StreamingBus]" in line and "publish:" in line:
        return True
    if "[DEBUG]" in line and "streaming_bus" in line.lower():
        return True
    if "autopilot_routes" in line.lower() and "[SSE]" in line and "chapter" in line.lower():
        return True
    return False


def shorten_log_message(text: str, max_chars: int = 88) -> str:
    """SSE / 终端展示固定上限，减轻 payload 与 DOM。"""
    t = (text or "").replace("\r\n", "\n").strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1] + "…"


def allocate_seq() -> int:
    """跨内存环与文件 tail 的全局单调序号（SSE 去重 / 重连）。"""
    global _seq
    with _lock:
        _seq += 1
        return _seq


def initial_snapshot_offset(log_path: str, max_bytes: int = 65536) -> int:
    """首次连接时从文件末尾附近开始读，避免整文件过大。"""
    path = Path(log_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return 0
    size = path.stat().st_size
    return max(0, size - max_bytes)


def file_end_offset(log_path: str) -> int:
    """重连时从文件末尾起只读新追加字节（不重复历史 tail）。"""
    path = Path(log_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return 0
    return path.stat().st_size


def read_incremental_log_file_lines(
    log_path: str,
    novel_id: str,
    cursor: int,
) -> Tuple[List[Dict], int]:
    """从独立进程写入的 LOG_FILE 增量 tail；行含 novel_id 时推送。

    返回 (行列表, 新字节偏移)。cursor 为上次读到的文件末尾位置。
    """
    path = Path(log_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return [], cursor
    size = path.stat().st_size
    if cursor > size:
        cursor = 0
    with path.open("rb") as f:
        f.seek(cursor)
        raw = f.read()
        new_cursor = f.tell()
    if not raw:
        return [], new_cursor
    if cursor > 0 and b"\n" in raw:
        first_nl = raw.find(b"\n")
        raw = raw[first_nl + 1 :]
    text = raw.decode("utf-8", errors="replace")
    lines_out: List[Dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or novel_id not in line:
            continue
        if should_skip_raw_log_file_line(line):
            continue
        lines_out.append(
            {
                "seq": allocate_seq(),
                "message": shorten_log_message(line),
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "logger": "file",
            }
        )
    return lines_out, new_cursor


def append_log_line(level: str, message: str, logger_name: str, timestamp_iso: str) -> None:
    """由 Handler 调用：写入全局环。"""
    if should_skip_autopilot_log_line(level, message, logger_name):
        return
    global _seq
    novel_id = _extract_novel_id(message)
    with _lock:
        _seq += 1
        seq = _seq
        _ring.append(
            AutopilotLogEntry(
                seq=seq,
                timestamp_iso=timestamp_iso,
                level=level,
                message=message,
                logger_name=logger_name,
                novel_id=novel_id,
            )
        )


def iter_new_for_novel(novel_id: str, after_seq: int, limit: int = 500) -> List[AutopilotLogEntry]:
    """返回 seq > after_seq 且与本书相关的日志行（时间顺序）。"""
    out: List[AutopilotLogEntry] = []
    with _lock:
        for e in _ring:
            if e.seq <= after_seq:
                continue
            if should_skip_autopilot_log_line(e.level, e.message, e.logger_name):
                continue
            if _matches_novel(e, novel_id):
                out.append(e)
                if len(out) >= limit:
                    break
    return out


def snapshot_for_novel(novel_id: str, limit: int = 400) -> List[AutopilotLogEntry]:
    """初次连接：返回本书最近若干条（用于冷启动即有上下文）。"""
    out: List[AutopilotLogEntry] = []
    with _lock:
        for e in reversed(_ring):
            if should_skip_autopilot_log_line(e.level, e.message, e.logger_name):
                continue
            if _matches_novel(e, novel_id):
                out.append(e)
                if len(out) >= limit:
                    break
    out.reverse()
    return out


class AutopilotRingLogHandler(logging.Handler):
    """将指定 logger 的日志写入内存环。"""

    def __init__(self) -> None:
        """初始化 `AutopilotRingLogHandler` 实例并注入运行所需的依赖与初始状态。

        调用方传入的协作者会被保存到实例上，后续方法复用这些依赖完成业务流程。

        返回: 无；初始化完成后状态保存在当前实例上。

        副作用: 不主动改变外部状态，除非传入对象本身在处理过程中被更新。
        """
        super().__init__(level=logging.DEBUG)

    def emit(self, record: logging.LogRecord) -> None:
        """同步执行 `emit` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `emit` 这一入口。
        关键输入:
        - record: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        try:
            msg = record.getMessage()
            if record.exc_info:
                msg = msg + "\n" + "".join(traceback.format_exception(*record.exc_info))
            ts = datetime.fromtimestamp(record.created).isoformat()
            append_log_line(record.levelname, msg, record.name, ts)
        except Exception:
            self.handleError(record)


def install_autopilot_log_ring_handler() -> None:
    """将环写入 Handler 挂到守护进程与自动驾驶 API logger（幂等）。"""
    global _handler_installed
    with _handler_lock:
        if _handler_installed:
            return
        h = AutopilotRingLogHandler()
        names = (
            "application.engine.services.autopilot_daemon",
            "interfaces.api.v1.engine.autopilot_routes",
        )
        for name in names:
            lg = logging.getLogger(name)
            if not any(isinstance(x, AutopilotRingLogHandler) for x in lg.handlers):
                lg.addHandler(h)
        _handler_installed = True
