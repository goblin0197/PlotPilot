"""Gemini LLM 提供商实现（官方 generateContent / streamGenerateContent 协议）"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from domain.ai.services.llm_service import GenerationConfig, GenerationResult
from domain.ai.value_objects.prompt import Prompt
from domain.ai.value_objects.token_usage import TokenUsage
from infrastructure.ai.config.settings import Settings
from .base import BaseProvider
from .model_resolution import require_resolved_model_id

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'


class GeminiProvider(BaseProvider):
    """定义 `GeminiProvider`，作为基础设施层中的业务对象。

    职责: 承载本模块的状态、规则或协作入口。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    def __init__(self, settings: Settings):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - settings: 配置对象或选项集合，控制执行策略与边界。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        super().__init__(settings)
        if not settings.api_key:
            raise ValueError('API key is required for GeminiProvider')
        self.base_url = (settings.base_url or DEFAULT_BASE_URL).rstrip('/')

    async def generate(self, prompt: Prompt, config: GenerationConfig) -> GenerationResult:
        """异步执行 `generate` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `generate` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        关键输出: `GenerationResult`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能发起网络或接口调用；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 会显式抛出 `RuntimeError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        model_id = require_resolved_model_id(
            config.model,
            self.settings.default_model,
            provider_label="Gemini",
        )
        payload = self._build_payload(prompt, config)
        query = self._build_query()
        url = self._build_url(model_id, 'generateContent')
        timeout = httpx.Timeout(self.settings.timeout_seconds)

        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            response = await client.post(
                url,
                params=query,
                headers=self._build_headers(stream=False),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = self._extract_text(data)
        if not content.strip():
            raise RuntimeError('Gemini returned empty content')

        usage = data.get('usageMetadata') or {}
        token_usage = TokenUsage(
            input_tokens=int(usage.get('promptTokenCount') or 0),
            output_tokens=int(usage.get('candidatesTokenCount') or 0),
        )
        return GenerationResult(content=content, token_usage=token_usage)

    async def stream_generate(self, prompt: Prompt, config: GenerationConfig) -> AsyncIterator[str]:
        """异步执行 `stream_generate` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `stream_generate` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        关键输出: `AsyncIterator[str]`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能发起网络或接口调用；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        model_id = require_resolved_model_id(
            config.model,
            self.settings.default_model,
            provider_label="Gemini",
        )
        payload = self._build_payload(prompt, config)
        query = self._build_query({'alt': 'sse'})
        url = self._build_url(model_id, 'streamGenerateContent')
        timeout = httpx.Timeout(self.settings.timeout_seconds)

        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            async with client.stream(
                'POST',
                url,
                params=query,
                headers=self._build_headers(stream=True),
                json=payload,
            ) as response:
                response.raise_for_status()
                buffer = ''
                async for chunk in response.aiter_text():
                    buffer += chunk.replace('\r\n', '\n')
                    while '\n\n' in buffer:
                        event_text, buffer = buffer.split('\n\n', 1)
                        text = self._parse_sse_event(event_text)
                        if text:
                            yield text

    def _build_url(self, model: str, action: str) -> str:
        """同步执行 `_build_url` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_url` 这一入口。
        关键输入:
        - model: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - action: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        model_name = model.strip()
        if not model_name:
            raise ValueError('Gemini: 构建请求 URL 时模型名为空')
        return f'{self.base_url}/models/{model_name}:{action}'

    def _build_query(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """同步执行 `_build_query` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_query` 这一入口。
        关键输入:
        - extra: `dict[str, Any] | None` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        query: dict[str, Any] = {'key': self.settings.api_key}
        query.update(self.settings.extra_query or {})
        if extra:
            query.update(extra)
        return query

    def _build_headers(self, *, stream: bool) -> dict[str, str]:
        """同步执行 `_build_headers` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_headers` 这一入口。
        关键输入:
        - stream: `bool` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `dict[str, str]`；包含后续流程所需字段的结构化映射。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        headers = {'Content-Type': 'application/json'}
        if stream:
            headers['Accept'] = 'text/event-stream'
        headers.update(self.settings.extra_headers or {})
        return headers

    def _build_payload(self, prompt: Prompt, config: GenerationConfig) -> dict[str, Any]:
        """同步执行 `_build_payload` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_payload` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        关键输出: `dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        generation_config = {
            'temperature': config.temperature,
            'maxOutputTokens': config.max_tokens,
        }
        payload: dict[str, Any] = {
            'contents': [
                {
                    'role': 'user',
                    'parts': [{'text': prompt.user}],
                }
            ],
            'generationConfig': generation_config,
        }
        if prompt.system.strip():
            payload['systemInstruction'] = {
                'parts': [{'text': prompt.system}],
            }
        extra_body = dict(self.settings.extra_body or {})
        generation_override = extra_body.pop('generationConfig', None)
        if isinstance(generation_override, dict):
            payload['generationConfig'].update(generation_override)
        payload.update(extra_body)
        return payload

    def _extract_text(self, data: dict[str, Any]) -> str:
        """同步执行 `_extract_text` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_extract_text` 这一入口。
        关键输入:
        - data: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        pieces: list[str] = []
        for candidate in data.get('candidates') or []:
            content = candidate.get('content') or {}
            for part in content.get('parts') or []:
                if part.get('thought') is True:
                    continue
                text = part.get('text')
                if text:
                    pieces.append(str(text))
        return ''.join(pieces)

    def _parse_sse_event(self, event_text: str) -> str:
        """同步执行 `_parse_sse_event` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_parse_sse_event` 这一入口。
        关键输入:
        - event_text: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        data_lines: list[str] = []
        for line in event_text.splitlines():
            if line.startswith('data:'):
                data_lines.append(line[5:].strip())

        if not data_lines:
            return ''

        raw_payload = ''.join(data_lines).strip()
        if not raw_payload or raw_payload == '[DONE]':
            return ''

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.debug('Gemini SSE parse skip: %s', raw_payload[:120])
            return ''

        if isinstance(payload, list):
            return ''.join(self._extract_text(item) for item in payload if isinstance(item, dict))
        if isinstance(payload, dict):
            return self._extract_text(payload)
        return ''
