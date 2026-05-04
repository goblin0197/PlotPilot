from __future__ import annotations

from typing import Optional


def _strip_known_suffix(url: str, suffixes: tuple[str, ...]) -> str:
    """同步执行 `_strip_known_suffix` 对应的业务步骤。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_strip_known_suffix` 这一入口。
    关键输入:
    - url: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
    - suffixes: `tuple[str, ...]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `str`；具体语义由调用场景和返回类型共同约束。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    normalized = (url or '').strip().rstrip('/')
    lower = normalized.lower()
    for suffix in suffixes:
        if lower.endswith(suffix):
            return normalized[: -len(suffix)].rstrip('/')
    return normalized


def normalize_openai_base_url(url: Optional[str]) -> Optional[str]:
    """同步转换或规范化 `openai_base_url` 相关的数据结构。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `normalize_openai_base_url` 这一入口。
    关键输入:
    - url: `Optional[str]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `Optional[str]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if not url or not str(url).strip():
        return None
    return _strip_known_suffix(
        str(url),
        (
            '/chat/completions',
            '/v1/chat/completions',
            '/completions',
        ),
    )


def normalize_anthropic_base_url(url: Optional[str]) -> Optional[str]:
    """同步转换或规范化 `anthropic_base_url` 相关的数据结构。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `normalize_anthropic_base_url` 这一入口。
    关键输入:
    - url: `Optional[str]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `Optional[str]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if not url or not str(url).strip():
        return None
    return _strip_known_suffix(
        str(url),
        (
            '/v1/messages',
            '/messages',
        ),
    )


def normalize_gemini_base_url(url: Optional[str]) -> Optional[str]:
    """同步转换或规范化 `gemini_base_url` 相关的数据结构。

    职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `normalize_gemini_base_url` 这一入口。
    关键输入:
    - url: `Optional[str]` 类型的业务输入，参与本函数的主要计算或流程控制。
    关键输出: `Optional[str]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    if not url or not str(url).strip():
        return None
    return _strip_known_suffix(
        str(url),
        (
            '/models',
            '/v1beta/models',
            '/v1/models',
        ),
    )
