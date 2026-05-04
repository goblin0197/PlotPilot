import logging
import os
from domain.ai.services.llm_service import LLMService, GenerationConfig
from domain.ai.value_objects.prompt import Prompt
from domain.novel.value_objects.chapter_state import ChapterState
from application.ai.chapter_state_llm_contract import (
    build_chapter_state_extraction_system_prompt,
    chapter_state_payload_to_domain,
    empty_chapter_state,
    parse_chapter_state_llm_response,
)

logger = logging.getLogger(__name__)


class StateExtractor:
    """状态提取应用服务

    使用 LLM 从章节内容中提取结构化信息
    """

    def __init__(self, llm_service: LLMService):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - llm_service: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.llm_service = llm_service

    async def extract_chapter_state(self, content: str) -> ChapterState:
        """从章节内容中提取状态

        Args:
            content: 章节内容

        Returns:
            提取的章节状态
        """
        logger.info(f"StateExtractor.extract_chapter_state: content_length={len(content)}")

        # 构建提取提示词
        system_prompt, user_prompt = self._build_extraction_prompt(content)
        prompt = Prompt(system=system_prompt, user=user_prompt)

        # 配置 LLM
        config = GenerationConfig(
            model=os.getenv("WRITING_MODEL", ""),
            max_tokens=4096,
            temperature=0.3
        )

        # 调用 LLM 生成
        result = await self.llm_service.generate(prompt=prompt, config=config)
        raw_response = result.content
        logger.debug(f"StateExtractor LLM raw response (first 500 chars): {raw_response[:500]}")

        payload, errors = parse_chapter_state_llm_response(raw_response)
        if payload is None:
            logger.warning(
                "StateExtractor: LLM 输出未通过契约校验: %s",
                "; ".join(errors) if errors else "unknown",
            )
            chapter_state = empty_chapter_state()
        else:
            chapter_state = chapter_state_payload_to_domain(payload)
        logger.info(
            f"StateExtractor result: "
            f"new_characters={len(chapter_state.new_characters)}, "
            f"character_actions={len(chapter_state.character_actions)}, "
            f"relationship_changes={len(chapter_state.relationship_changes)}, "
            f"foreshadowing_planted={len(chapter_state.foreshadowing_planted)}, "
            f"foreshadowing_resolved={len(chapter_state.foreshadowing_resolved)}, "
            f"events={len(chapter_state.events)}"
        )
        return chapter_state

    def _build_extraction_prompt(self, content: str) -> tuple[str, str]:
        """构建提取提示词

        Args:
            content: 章节内容

        Returns:
            (system_prompt, user_prompt) 元组
        """
        system_prompt = build_chapter_state_extraction_system_prompt()

        user_prompt = f"""请从以下章节内容中提取结构化信息：

{content}"""

        return system_prompt, user_prompt
