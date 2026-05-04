from __future__ import annotations

from typing import AsyncIterator

from application.ai.llm_control_service import LLMControlService, LLMProfile
from domain.ai.services.llm_service import GenerationConfig, GenerationResult, LLMService
from domain.ai.value_objects.prompt import Prompt
from infrastructure.ai.config.settings import Settings
from infrastructure.ai.providers.anthropic_provider import AnthropicProvider
from infrastructure.ai.providers.gemini_provider import GeminiProvider
from infrastructure.ai.providers.mock_provider import MockProvider
from infrastructure.ai.providers.openai_provider import OpenAIProvider
from infrastructure.ai.url_utils import (
    normalize_anthropic_base_url,
    normalize_gemini_base_url,
    normalize_openai_base_url,
)

_DEFAULT_CONFIG = GenerationConfig()


class LLMProviderFactory:
    """定义 `LLMProviderFactory`，作为基础设施层中的业务对象。

    职责: 承载本模块的状态、规则或协作入口。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    def __init__(self, control_service: Optional[LLMControlService] = None):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - control_service: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.control_service = control_service or LLMControlService()

    def create_from_profile(self, profile: Optional[LLMProfile]) -> LLMService:
        """同步组装 `profile` 所需的结构化结果。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `create_from_profile` 这一入口。
        关键输入:
        - profile: 文件系统路径，函数会据此读取、写入或定位资源。
        关键输出: `LLMService`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if profile is None:
            return MockProvider()

        resolved = self.control_service.resolve_profile(profile)
        if not resolved.api_key.strip() or not resolved.model.strip():
            return MockProvider()

        settings = self._profile_to_settings(resolved)
        if resolved.protocol == 'anthropic':
            return AnthropicProvider(settings)
        if resolved.protocol == 'gemini':
            return GeminiProvider(settings)
        return OpenAIProvider(settings)

    def create_active_provider(self) -> LLMService:
        """同步组装 `active_provider` 所需的结构化结果。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `create_active_provider` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `LLMService`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self.create_from_profile(self.control_service.resolve_active_profile())

    def _profile_to_settings(self, profile: LLMProfile) -> Settings:
        """同步转换或规范化 `profile_settings` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_profile_to_settings` 这一入口。
        关键输入:
        - profile: 文件系统路径，函数会据此读取、写入或定位资源。
        关键输出: `Settings`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if profile.protocol == 'anthropic':
            normalized_base_url = normalize_anthropic_base_url(profile.base_url)
        elif profile.protocol == 'gemini':
            normalized_base_url = normalize_gemini_base_url(profile.base_url)
        else:
            normalized_base_url = normalize_openai_base_url(profile.base_url)

        return Settings(
            default_model=profile.model,
            default_temperature=profile.temperature,
            default_max_tokens=profile.max_tokens,
            api_key=profile.api_key,
            base_url=normalized_base_url,
            timeout_seconds=profile.timeout_seconds,
            extra_headers=profile.extra_headers,
            extra_query=profile.extra_query,
            extra_body=profile.extra_body,
            provider_name=profile.name,
            protocol=profile.protocol,
            use_legacy_chat_completions=profile.use_legacy_chat_completions,
        )


class DynamicLLMService(LLMService):
    """动态读取当前激活配置，适配长生命周期服务/守护进程。"""

    def __init__(self, factory: Optional[LLMProviderFactory] = None):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - factory: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.factory = factory or LLMProviderFactory()

    def _resolve_provider(self) -> LLMService:
        """同步执行 `_resolve_provider` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_resolve_provider` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `LLMService`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self.factory.create_active_provider()

    @staticmethod
    def _merge_config(config: GenerationConfig, provider: LLMService) -> GenerationConfig:
        """同步执行 `_merge_config` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_merge_config` 这一入口。
        关键输入:
        - config: 配置对象或选项集合，控制执行策略与边界。
        - provider: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: `GenerationConfig`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        settings = getattr(provider, 'settings', None)
        if settings is None:
            return config

        model = config.model
        if not model or model == _DEFAULT_CONFIG.model:
            model = settings.default_model

        max_tokens = config.max_tokens
        if max_tokens == _DEFAULT_CONFIG.max_tokens:
            max_tokens = settings.default_max_tokens

        temperature = config.temperature
        if temperature == _DEFAULT_CONFIG.temperature:
            temperature = settings.default_temperature

        return GenerationConfig(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    async def generate(self, prompt: Prompt, config: GenerationConfig) -> GenerationResult:
        """异步执行 `generate` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `generate` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        关键输出: `GenerationResult`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能调用 LLM、向量检索或生成链路；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        provider = self._resolve_provider()
        effective_config = self._merge_config(config, provider)
        return await provider.generate(prompt, effective_config)

    async def stream_generate(self, prompt: Prompt, config: GenerationConfig) -> AsyncIterator[str]:
        """异步执行 `stream_generate` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `stream_generate` 这一入口。
        关键输入:
        - prompt: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - config: 配置对象或选项集合，控制执行策略与边界。
        关键输出: `AsyncIterator[str]`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能调用 LLM、向量检索或生成链路；会在事件循环中等待异步 I/O 或后台任务。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        provider = self._resolve_provider()
        effective_config = self._merge_config(config, provider)
        async for chunk in provider.stream_generate(prompt, effective_config):
            yield chunk
