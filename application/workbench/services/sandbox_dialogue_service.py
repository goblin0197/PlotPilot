"""Sandbox dialogue service for managing dialogue whitelist and grounded prompts."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from application.workbench.dtos.sandbox_dto import DialogueEntry, DialogueWhitelistResponse
from domain.ai.value_objects.prompt import Prompt


class SandboxDialogueService:
    """Service for sandbox dialogue whitelist and grounded character dialogue prompts."""

    def __init__(self, narrative_event_repository):
        """
        Initialize the service.

        Args:
            narrative_event_repository: Repository for accessing narrative events
        """
        self.narrative_event_repository = narrative_event_repository

    def get_dialogue_whitelist(
        self,
        novel_id: str,
        chapter_number: Optional[int] = None,
        speaker: Optional[str] = None
    ) -> DialogueWhitelistResponse:
        """
        Get dialogue whitelist for sandbox simulation.

        Args:
            novel_id: Novel ID
            chapter_number: Optional chapter filter
            speaker: Optional speaker filter

        Returns:
            DialogueWhitelistResponse containing filtered dialogues
        """
        events = self.narrative_event_repository.list_up_to_chapter(
            novel_id, max_chapter_inclusive=9999
        )

        dialogues: list[DialogueEntry] = []

        for event in events:
            dialogue_entry = self._event_to_dialogue_entry(event)
            if dialogue_entry is None:
                continue

            if chapter_number is not None and dialogue_entry.chapter != chapter_number:
                continue

            if speaker is not None and dialogue_entry.speaker != speaker:
                continue

            dialogues.append(dialogue_entry)

        return DialogueWhitelistResponse(dialogues=dialogues, total_count=len(dialogues))

    def get_recent_character_dialogues(
        self,
        novel_id: str,
        speaker: str,
        limit: int = 4,
    ) -> list[DialogueEntry]:
        """Get the most recent dialogue samples for a character."""
        if not speaker or limit <= 0:
            return []

        entries = self.get_dialogue_whitelist(novel_id=novel_id, speaker=speaker).dialogues
        entries.sort(key=lambda item: (item.chapter, item.dialogue_id), reverse=True)
        return entries[:limit]

    def build_dialogue_generation_prompt(
        self,
        *,
        character: Any,
        scene_prompt: str,
        mental_state: str,
        verbal_tic: str,
        idle_behavior: str,
        all_characters: Optional[Iterable[Any]] = None,
        recent_dialogues: Optional[Iterable[DialogueEntry]] = None,
    ) -> Prompt:
        """Build a grounded prompt for character dialogue generation."""
        character_name = self._stringify(getattr(character, "name", ""))
        description = self._stringify(getattr(character, "description", ""))
        public_profile = self._stringify(getattr(character, "public_profile", ""))
        relationships = list(getattr(character, "relationships", []) or [])
        scene_related_characters = self._find_scene_related_characters(
            scene_prompt=scene_prompt,
            target_character=character,
            all_characters=all_characters,
        )

        system = (
            "你是长篇小说的角色对白润色器。"
            "你的任务是让指定角色在给定场景里说出符合其人设、关系位置、历史声线和当前心理锚点的话。"
            "优先级：历史对白习惯 > 角色设定 > 当前心理状态/口头禅/动作 > 场景目标。"
            "不要输出分析、设定说明、JSON、标题或额外注释。"
            "如果场景里出现其他角色，他们只能作为陪衬，不能抢走目标角色的口吻与主导发言权。"
        )

        relationship_block = self._format_relationships(relationships)
        history_block = self._format_recent_dialogues(recent_dialogues)
        related_block = self._format_scene_related_characters(scene_related_characters)
        scene_text = self._stringify(scene_prompt) or "（未提供场景）"

        user = f"""目标角色：{character_name}

【角色基础设定】
- 人设描述：{description or "暂无"}
- 公开档案：{public_profile or "暂无"}
- 当前心理状态：{mental_state or "NORMAL"}
- 口头禅：{verbal_tic or "无"}
- 常见动作：{idle_behavior or "无"}

【角色关系】
{relationship_block}

【场景点名的相关角色】
{related_block}

【历史对白样本（模仿语气，不要照抄）】
{history_block}

【当前场景】
{scene_text}

请直接生成这名角色在当前场景中的一小段对白，要求：
1. 只写成品台词，可夹带极少量动作描写；
2. 重点保持这个角色自己的语气、身份位置和情绪，不要串成别的角色；
3. 若场景里有其他角色，可以被提及或简短回应，但不要让其他角色成为主说话人；
4. 长度控制在 2-4 句话；
5. 不要输出角色名标签、分析说明、引号外注释。"""

        return Prompt(system=system, user=user)

    def clean_generated_dialogue(self, content: str, character_name: str) -> str:
        """Normalize generated dialogue for UI rendering."""
        text = self._stringify(content)
        if not text:
            return ""

        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

        for prefix in (
            f"{character_name}：",
            f"{character_name}:",
            "对白：",
            "对白:",
            "台词：",
            "台词:",
            "对话：",
            "对话:",
        ):
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        if len(text) >= 2:
            for left, right in (("“", "”"), ('"', '"'), ("「", "」")):
                if text.startswith(left) and text.endswith(right):
                    text = text[1:-1].strip()
                    break

        return text

    def _event_to_dialogue_entry(self, event: dict) -> Optional[DialogueEntry]:
        """同步执行 `_event_to_dialogue_entry` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_event_to_dialogue_entry` 这一入口。
        关键输入:
        - event: `dict` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `Optional[DialogueEntry]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        tags = event.get("tags") or []
        dialogue_tag = next(
            (tag for tag in tags if tag.startswith("对话:") or tag.startswith("对白:")),
            None,
        )
        if not dialogue_tag:
            return None

        speaker = dialogue_tag.split(":", 1)[1].strip() if ":" in dialogue_tag else ""
        if not speaker:
            return None

        summary = self._stringify(event.get("event_summary", ""))
        content = self._strip_speaker_prefix(summary, speaker) or summary
        context = self._extract_scene_context(tags)

        return DialogueEntry(
            dialogue_id=self._stringify(event.get("event_id", "")),
            chapter=int(event.get("chapter_number", 0) or 0),
            speaker=speaker,
            content=content,
            context=context,
            tags=tags,
        )

    @staticmethod
    def _stringify(value: Any) -> str:
        """同步执行 `_stringify` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_stringify` 这一入口。
        关键输入:
        - value: 待校验、转换或写入的值，类型约束为 `Any`。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return str(value or "").strip()

    def _strip_speaker_prefix(self, summary: str, speaker: str) -> str:
        """同步执行 `_strip_speaker_prefix` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_strip_speaker_prefix` 这一入口。
        关键输入:
        - summary: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - speaker: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        for prefix in (f"{speaker}:", f"{speaker}："):
            if summary.startswith(prefix):
                return summary[len(prefix):].strip()
        return summary

    def _extract_scene_context(self, tags: list[str]) -> str:
        """同步执行 `_extract_scene_context` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_extract_scene_context` 这一入口。
        关键输入:
        - tags: `list[str]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        scene_tag = next((tag for tag in tags if tag.startswith("场景:")), "")
        return scene_tag.split(":", 1)[1].strip() if ":" in scene_tag else ""

    def _format_relationships(self, relationships: list[Any]) -> str:
        """同步执行 `_format_relationships` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_format_relationships` 这一入口。
        关键输入:
        - relationships: `list[Any]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if not relationships:
            return "- 暂无明确关系记录"

        lines: list[str] = []
        for relationship in relationships[:6]:
            rendered = self._render_relationship(relationship)
            if rendered:
                lines.append(f"- {rendered}")
        return "\n".join(lines) if lines else "- 暂无明确关系记录"

    def _render_relationship(self, relationship: Any) -> str:
        """同步执行 `_render_relationship` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_render_relationship` 这一入口。
        关键输入:
        - relationship: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if isinstance(relationship, dict):
            target = self._first_non_empty(
                relationship.get("target_name"),
                relationship.get("target"),
                relationship.get("character"),
                relationship.get("name"),
                relationship.get("to"),
                relationship.get("other"),
            )
            relation = self._first_non_empty(
                relationship.get("relation"),
                relationship.get("type"),
                relationship.get("label"),
                relationship.get("status"),
                relationship.get("description"),
            )
            if target and relation:
                return f"{target}：{relation}"
            if relation:
                return relation
            if target:
                return target
            return self._stringify(relationship)

        return self._stringify(relationship)

    def _find_scene_related_characters(
        self,
        *,
        scene_prompt: str,
        target_character: Any,
        all_characters: Optional[Iterable[Any]],
    ) -> list[dict[str, str]]:
        """同步执行 `_find_scene_related_characters` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_find_scene_related_characters` 这一入口。
        关键输入:
        - scene_prompt: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - target_character: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
        - all_characters: `Optional[Iterable[Any]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `list[dict[str, str]]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        prompt_text = self._stringify(scene_prompt)
        if not prompt_text or not all_characters:
            return []

        target_name = self._stringify(getattr(target_character, "name", ""))
        relationships = list(getattr(target_character, "relationships", []) or [])
        related: list[dict[str, str]] = []

        for other in all_characters:
            other_name = self._stringify(getattr(other, "name", ""))
            if not other_name or other_name == target_name:
                continue
            if other_name not in prompt_text:
                continue

            related.append(
                {
                    "name": other_name,
                    "description": self._stringify(getattr(other, "description", "")),
                    "relation": self._find_relationship_to_name(other_name, relationships),
                }
            )

        return related[:3]

    def _find_relationship_to_name(self, other_name: str, relationships: list[Any]) -> str:
        """同步执行 `_find_relationship_to_name` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_find_relationship_to_name` 这一入口。
        关键输入:
        - other_name: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - relationships: `list[Any]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        for relationship in relationships:
            if isinstance(relationship, dict):
                relation_label = self._relationship_label(relationship)
                haystack = " ".join(
                    self._stringify(item)
                    for item in (
                        relationship.get("target_name"),
                        relationship.get("target"),
                        relationship.get("character"),
                        relationship.get("name"),
                        relationship.get("to"),
                        relationship.get("other"),
                        relationship.get("relation"),
                        relationship.get("type"),
                        relationship.get("label"),
                        relationship.get("status"),
                        relationship.get("description"),
                    )
                    if self._stringify(item)
                )
                if other_name in haystack:
                    return relation_label or self._render_relationship(relationship)
            else:
                text = self._stringify(relationship)
                if other_name in text:
                    return text

        return ""

    def _relationship_label(self, relationship: dict[str, Any]) -> str:
        """同步执行 `_relationship_label` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_relationship_label` 这一入口。
        关键输入:
        - relationship: `dict[str, Any]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self._first_non_empty(
            relationship.get("relation"),
            relationship.get("type"),
            relationship.get("label"),
            relationship.get("status"),
            relationship.get("description"),
        )

    def _format_scene_related_characters(self, related_characters: list[dict[str, str]]) -> str:
        """同步执行 `_format_scene_related_characters` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_format_scene_related_characters` 这一入口。
        关键输入:
        - related_characters: `list[dict[str, str]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if not related_characters:
            return "- 场景描述里未点名其他已知角色"

        lines: list[str] = []
        for item in related_characters:
            pieces = [item["name"]]
            if item.get("relation"):
                pieces.append(f"关系：{item['relation']}")
            if item.get("description"):
                pieces.append(f"描述：{item['description']}")
            lines.append(f"- {'；'.join(pieces)}")
        return "\n".join(lines)

    def _format_recent_dialogues(self, recent_dialogues: Optional[Iterable[DialogueEntry]]) -> str:
        """同步执行 `_format_recent_dialogues` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_format_recent_dialogues` 这一入口。
        关键输入:
        - recent_dialogues: `Optional[Iterable[DialogueEntry]]` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        dialogues = list(recent_dialogues or [])
        if not dialogues:
            return "- 暂无历史对白样本"

        lines: list[str] = []
        for entry in dialogues[:4]:
            if entry.context:
                lines.append(f"- 第{entry.chapter}章 / {entry.context}：{entry.content}")
            else:
                lines.append(f"- 第{entry.chapter}章：{entry.content}")
        return "\n".join(lines)

    @staticmethod
    def _first_non_empty(*values: Any) -> str:
        """同步执行 `_first_non_empty` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_first_non_empty` 这一入口。
        关键输入:
        - *values: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""
