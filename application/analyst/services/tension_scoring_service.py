"""独立多维张力分析服务。

将张力评分从 llm_chapter_extract_bundle() 的多任务 JSON 提取中拆出，
使用专门的多维 prompt（情节/情绪/节奏）进行精准分析。
"""
from __future__ import annotations

import logging
from typing import Optional

from domain.ai.services.llm_service import LLMService, GenerationConfig
from domain.ai.value_objects.prompt import Prompt
from domain.novel.value_objects.tension_dimensions import TensionDimensions
from application.ai.tension_scoring_contract import (
    TensionScoringLlmPayload,
    tension_scoring_payload_to_domain,
    tension_scoring_response_format,
)
from application.ai.structured_json_pipeline import structured_json_generate
from infrastructure.ai.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)

# 章节正文最大长度（与 llm_chapter_extract_bundle 保持一致）
_MAX_CONTENT_LENGTH = 24000

# PromptManager / DB 不可用时使用的兜底 system
_FALLBACK_TEMPLATE = """你是专业的网文叙事张力分析师。你的任务是分析章节正文的多维张力。

## 评分维度（每项 0-100 整数）

### 1. 情节张力 (plot_tension)
衡量冲突强度、悬念密度和信息不对称程度。
### 2. 情绪张力 (emotional_tension)
衡量角色情绪波动幅度和读者共情深度。
### 3. 节奏张力 (pacing_tension)
衡量场景切换频率、叙述节奏和信息密度。

前章综合张力约为 {prev_tension}/100。

输出 JSON：{{"plot_tension": 0, "emotional_tension": 0, "pacing_tension": 0, "plot_justification": "", "emotional_justification": "", "pacing_justification": ""}}"""


class TensionScoringService:
    """独立多维张力分析服务。

    对章节正文进行三维度（情节张力、情绪张力、节奏张力）评分，
    并通过加权公式计算综合张力分。
    """

    def __init__(self, llm_service: LLMService) -> None:
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - llm_service: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self._llm = llm_service

    async def score_chapter(
        self,
        chapter_content: str,
        chapter_number: int,
        prev_chapter_tension: float = 50.0,
    ) -> TensionDimensions:
        """分析章节的多维张力。

        Args:
            chapter_content: 章节正文
            chapter_number: 章节号
            prev_chapter_tension: 前章综合张力（0-100），用于提供上下文基准

        Returns:
            TensionDimensions 多维张力结果
        """
        body = chapter_content.strip()
        if not body:
            return TensionDimensions.neutral()
        if len(body) > _MAX_CONTENT_LENGTH:
            body = body[:_MAX_CONTENT_LENGTH] + "\n\n…（正文过长已截断）"

        prompt = Prompt(
            system=self._build_system_prompt(prev_chapter_tension),
            user=f"第 {chapter_number} 章正文如下：\n\n{body}",
        )
        config = GenerationConfig(
            max_tokens=512,
            temperature=0.3,
            response_format=tension_scoring_response_format(),
        )

        try:
            payload = await structured_json_generate(
                llm=self._llm,
                prompt=prompt,
                config=config,
                schema_model=TensionScoringLlmPayload,
            )
        except Exception as e:
            logger.warning("张力评分管线异常: %s", e)
            payload = None

        if payload is None:
            return TensionDimensions.neutral()

        dims = tension_scoring_payload_to_domain(payload)
        logger.debug(
            "张力评分完成: plot=%.0f emotional=%.0f pacing=%.0f composite=%.1f",
            dims.plot_tension,
            dims.emotional_tension,
            dims.pacing_tension,
            dims.composite_score,
        )
        return dims

    # ------------------------------------------------------------------
    # Prompt 构建
    # ------------------------------------------------------------------

    @staticmethod
    def _build_system_prompt(prev_tension: float) -> str:
        """同步执行 `_build_system_prompt` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_build_system_prompt` 这一入口。
        关键输入:
        - prev_tension: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        mgr = get_prompt_manager()
        mgr.ensure_seeded()
        prev = f"{prev_tension:.0f}"
        rendered = mgr.render("tension-scoring", {"prev_tension": prev})
        if rendered and (rendered.get("system") or "").strip():
            return rendered["system"]
        return _FALLBACK_TEMPLATE.format(prev_tension=prev)
