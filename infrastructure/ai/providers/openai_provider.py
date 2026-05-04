"""OpenAI LLM 提供商实现"""
import logging
import openai
import httpx
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from domain.ai.services.llm_service import GenerationConfig, GenerationResult
from domain.ai.value_objects.prompt import Prompt
from domain.ai.value_objects.token_usage import TokenUsage
from infrastructure.ai.config.settings import Settings
from .base import BaseProvider
from .model_resolution import require_resolved_model_id

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI LLM 提供商实现

    通过 use_legacy_chat_completions 显式选择协议：
    - False（默认）：走 Responses API，失败时自动降级到 Chat Completions
    - True：走 Chat Completions API
    """

    # 静态类级别缓存：记录哪些 base_url 不支持 Responses API，从而避免重复降级带来的延迟开销
    _fallback_to_chat_cache: set[str] = set()

    def __init__(self, settings: Settings):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - settings: 配置对象或选项集合，控制执行策略与边界。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 可能发起网络或接口调用。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        super().__init__(settings)

        if not settings.api_key:
            raise ValueError("API key is required for OpenAIProvider")

        self._use_legacy = settings.use_legacy_chat_completions

        client_kwargs = {
            "api_key": settings.api_key,
            "timeout": settings.timeout_seconds,
            "default_headers": settings.extra_headers or None,
            "default_query": settings.extra_query or None,
        }
        if settings.base_url:
            client_kwargs["base_url"] = settings.base_url

        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.timeout_seconds),
            trust_env=False,
        )
        client_kwargs["http_client"] = self._http_client
        self.async_client = AsyncOpenAI(**client_kwargs)

    async def generate(
        self,
        prompt: Prompt,
        config: GenerationConfig
    ) -> GenerationResult:
        """异步执行 `generate` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `generate` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        关键输出: `GenerationResult`；具体语义由调用场景和返回类型共同约束。
        副作用: 会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 会显式抛出 `RuntimeError, except`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        try:
            base_url = self.settings.base_url or "https://api.openai.com/v1"
            use_responses = not self._use_legacy and base_url not in self.__class__._fallback_to_chat_cache

            if use_responses:
                try:
                    return await self._generate_via_responses(prompt, config)
                except (openai.NotFoundError, openai.BadRequestError, RuntimeError) as e:
                    logger.info(f"Responses API unsupported for {base_url}, falling back to chat completions: {str(e)}")
                    self.__class__._fallback_to_chat_cache.add(base_url)
                except Exception as e:
                    # 某些网关在路径错误时可能不抛严格的 404 而是抛出其他错误，如果消息含有明确路径错误也尝试降级
                    if "404" in str(e) or "Not Found" in str(e) or "400" in str(e) or "Account invalid" in str(e) or "INVALID_ARGUMENT" in str(e) or "401" in str(e) or "未登录" in str(e):
                        logger.info(f"Gateway returned error for Responses API ({base_url}), falling back: {str(e)}")
                        self.__class__._fallback_to_chat_cache.add(base_url)
                    else:
                        raise

            # 使用降级的 Chat Completions API
            return await self._generate_via_chat(prompt, config)
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to generate text: {str(e)}") from e

    async def _generate_via_chat(self, prompt: Prompt, config: GenerationConfig) -> GenerationResult:
        """Chat Completions API 非流式生成"""
        messages = self._build_messages(prompt)
        request_kwargs = self._build_chat_request_kwargs(messages, config)

        response = await self.async_client.chat.completions.create(**request_kwargs)
        content = self._extract_text_from_response(response)

        if not content:
            logger.warning(
                "OpenAI-compatible response returned empty non-stream content; "
                "falling back to streaming aggregation"
            )
            content, token_usage = await self._generate_via_stream(request_kwargs)
            return GenerationResult(content=content, token_usage=token_usage)

        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        return GenerationResult(
            content=content,
            token_usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
        )

    async def stream_generate(
        self,
        prompt: Prompt,
        config: GenerationConfig
    ) -> AsyncIterator[str]:
        """异步执行 `stream_generate` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `stream_generate` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        关键输出: `AsyncIterator[str]`；具体语义由调用场景和返回类型共同约束。
        副作用: 会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 会显式抛出 `RuntimeError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        try:
            base_url = self.settings.base_url or "https://api.openai.com/v1"
            use_responses = not self._use_legacy and base_url not in self.__class__._fallback_to_chat_cache

            if use_responses:
                try:
                    # 尝试走 Responses 流式 API
                    request_kwargs = self._build_responses_request_kwargs(prompt, config, stream=True)
                    stream = await self.async_client.responses.create(**request_kwargs)
                    async for chunk in stream:
                        content = self._extract_text_from_responses_chunk(chunk)
                        if content:
                            yield content
                    return  # 正常完成则结束 generator
                except (openai.NotFoundError, openai.BadRequestError):
                    self.__class__._fallback_to_chat_cache.add(base_url)
                    logger.info(f"Stream: Responses API unsupported for {base_url}, falling back.")
                except Exception as e:
                    if "404" in str(e) or "Not Found" in str(e) or "400" in str(e) or "Account invalid" in str(e) or "INVALID_ARGUMENT" in str(e) or "401" in str(e) or "未登录" in str(e):
                        self.__class__._fallback_to_chat_cache.add(base_url)
                        logger.info(f"Stream: Gateway returned error for Responses API ({base_url}), falling back.")
                    else:
                        logger.error(f"[Responses Stream] Failed: {e}")
                        raise

            # 降级：走原来的 Chat Completions 流式 API
            messages = self._build_messages(prompt)
            request_kwargs = self._build_chat_request_kwargs(messages, config, stream=True)
            stream = await self.async_client.chat.completions.create(**request_kwargs)
            async for chunk in stream:
                content = self._extract_text_from_stream_chunk(chunk)
                if content:
                    yield content
        except Exception as e:
            logger.error(f"[Stream] Failed: {e}")
            raise RuntimeError(f"Failed to stream text: {str(e)}") from e

    @staticmethod
    def _build_messages(prompt: Prompt) -> list[dict[str, str]]:
        """同步执行 `_build_messages` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_messages` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        关键输出: `list[dict[str, str]]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": prompt.user}
        ]

    def _build_chat_request_kwargs(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig,
        *,
        stream: bool = False,
    ) -> dict[str, Any]:
        """同步执行 `_build_chat_request_kwargs` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_chat_request_kwargs` 这一入口。
        关键输入:
        - messages: `list[dict[str, str]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        - config: 配置对象或选项集合，控制执行策略与边界。
        - stream: `bool` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        model_id = require_resolved_model_id(
            config.model,
            self.settings.default_model,
            provider_label="OpenAI 兼容",
        )
        kwargs: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "extra_headers": self.settings.extra_headers or None,
            "extra_query": self.settings.extra_query or None,
            "extra_body": self.settings.extra_body or None,
            "timeout": self.settings.timeout_seconds,
        }
        if stream:
            kwargs["stream"] = True
        return kwargs

    def _build_responses_request_kwargs(
        self,
        prompt: Prompt,
        config: GenerationConfig,
        *,
        stream: bool = False,
    ) -> dict[str, Any]:
        """同步执行 `_build_responses_request_kwargs` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_responses_request_kwargs` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        - stream: `bool` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        model_id = require_resolved_model_id(
            config.model,
            self.settings.default_model,
            provider_label="OpenAI 兼容",
        )
        kwargs: dict[str, Any] = {
            "model": model_id,
            "instructions": prompt.system,
            "input": [{"role": "user", "content": prompt.user}],
            "temperature": config.temperature,
            "max_output_tokens": config.max_tokens,
        }
        if self.settings.extra_body:
             kwargs.update(self.settings.extra_body)

        if stream:
            kwargs["stream"] = True
        return kwargs

    async def _generate_via_responses(self, prompt: Prompt, config: GenerationConfig) -> GenerationResult:
        """Responses API 非流式生成"""
        request_kwargs = self._build_responses_request_kwargs(prompt, config)
        response = await self.async_client.responses.create(**request_kwargs)

        output = getattr(response, "output", None)
        content_parts: list[str] = []
        if output:
            for item in output:
                if getattr(item, "type", "") == "message":
                    for part in getattr(item, "content", []):
                        if getattr(part, "type", "") == "text":
                            piece = str(getattr(part, "text", "")).strip()
                            if piece:
                                content_parts.append(piece)
        content = "\n".join(content_parts).strip()
        if not content:
            raise RuntimeError("Responses API returned empty content")

        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

        return GenerationResult(
            content=content,
            token_usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)
        )

    @staticmethod
    def _extract_text_from_responses_chunk(chunk: Any) -> str:
        """原生 Responses stream 解析封装"""
        try:
            event_type = getattr(chunk, "type", "")
            if event_type == "response.content_part.added":
                part = getattr(chunk, "part", None)
                if part and getattr(part, "type", "") == "text":
                    return getattr(part, "text", "")
            elif event_type == "message.delta":
                delta = getattr(chunk, "delta", None)
                if delta:
                     content = getattr(delta, "content", None)
                     if isinstance(content, str):
                         return content
        except Exception:
            pass
        return ""

    @staticmethod
    def _normalize_chat_completion_content(content: Any) -> str:
        """兼容 message.content 为 str 或多段 content part 列表（OpenAI 新协议与多数聚合网关）。"""
        if content is None:
            return ""
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    item_type = (item.get("type") or "").lower()
                    if item_type in ("reasoning", "thinking", "refusal"):
                        continue
                    text_val = item.get("text")
                    if isinstance(text_val, str) and text_val.strip():
                        parts.append(text_val)
                else:
                    text_attr = getattr(item, "text", None)
                    if isinstance(text_attr, str) and text_attr.strip():
                        parts.append(text_attr)
            return "\n".join(parts).strip()

        return str(content).strip()

    @staticmethod
    def _extract_text_from_response(response: Any) -> str:
        """同步执行 `_extract_text_from_response` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_extract_text_from_response` 这一入口。
        关键输入:
        - response: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if not getattr(response, "choices", None):
            return ""

        message = getattr(response.choices[0], "message", None)
        content = getattr(message, "content", None)
        return OpenAIProvider._normalize_chat_completion_content(content)

    @staticmethod
    def _extract_text_from_stream_chunk(chunk: Any) -> str:
        """同步执行 `_extract_text_from_stream_chunk` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_extract_text_from_stream_chunk` 这一入口。
        关键输入:
        - chunk: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if not getattr(chunk, "choices", None):
            return ""

        delta = getattr(chunk.choices[0], "delta", None)
        content = getattr(delta, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return OpenAIProvider._normalize_chat_completion_content(content)
        return ""

    async def _generate_via_stream(self, request_kwargs: dict[str, Any]) -> tuple[str, TokenUsage]:
        """异步执行 `_generate_via_stream` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_generate_via_stream` 这一入口。
        关键输入:
        - request_kwargs: `dict[str, Any]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `tuple[str, TokenUsage]`；按调用约定排序或过滤后的结果集合。
        副作用: 会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 会显式抛出 `RuntimeError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        stream = await self.async_client.chat.completions.create(
            **{**request_kwargs, "stream": True}
        )

        parts: list[str] = []
        input_tokens = 0
        output_tokens = 0

        async for chunk in stream:
            content = self._extract_text_from_stream_chunk(chunk)
            if content:
                parts.append(content)

            usage = getattr(chunk, "usage", None)
            if usage is not None:
                input_tokens = getattr(usage, "prompt_tokens", 0) or 0
                output_tokens = getattr(usage, "completion_tokens", 0) or 0

        content = "".join(parts).strip()
        if not content:
            raise RuntimeError("API returned empty content")

        return content, TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
