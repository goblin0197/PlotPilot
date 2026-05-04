"""CustomThemeSkillWrapper — 将用户自定义的提示词包装为 ThemeSkill 运行时实例

用户在前端填写的纯文本提示词会被存入 custom_theme_skills 表，
运行时通过此 Wrapper 类转换为标准 ThemeSkill 实例注入管线。
"""

from typing import Any, Dict, List

from application.engine.theme.theme_agent import ThemeSkill


class CustomThemeSkillWrapper(ThemeSkill):
    """用户自定义技能的运行时包装器

    将数据库中的纯文本提示词映射到 ThemeSkill 的 4 个注入点：

    - context_prompt → on_context_build()  上下文阶段注入
    - beat_prompt    → on_beat_enhance()   节拍阶段注入（根据 beat_triggers 过滤）
    - audit_checks   → on_audit_enhance()  审计阶段追加检查项
    """

    def __init__(self, data: Dict[str, Any]):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - data: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self._key: str = data["skill_key"]
        self._name: str = data["skill_name"]
        self._description: str = data.get("skill_description", "")
        self._compatible_genres: List[str] = data.get("compatible_genres", [])
        self._context_prompt: str = data.get("context_prompt", "")
        self._beat_prompt: str = data.get("beat_prompt", "")
        self._beat_triggers: str = data.get("beat_triggers", "")
        self._audit_checks: List[str] = data.get("audit_checks", [])

    # ─── 标识属性 ───

    @property
    def skill_key(self) -> str:
        """读取或计算 `skill_key` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_key` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self._key

    @property
    def skill_name(self) -> str:
        """读取或计算 `skill_name` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_name` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self._name

    @property
    def skill_description(self) -> str:
        """读取或计算 `skill_description` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `skill_description` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self._description

    @property
    def compatible_genres(self) -> List[str]:
        """读取或计算 `compatible_genres` 对应的派生值。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `compatible_genres` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `List[str]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self._compatible_genres

    # ─── 注入点 ───

    def on_context_build(
        self,
        novel_id: str,
        chapter_number: int,
        outline: str,
        existing_context: str,
    ) -> str:
        """上下文增强：直接返回用户填写的 context_prompt"""
        return self._context_prompt

    def on_beat_enhance(
        self,
        beat_description: str,
        beat_focus: str,
        chapter_number: int,
        outline: str,
    ) -> str:
        """节拍增强：根据 beat_triggers 关键词匹配后返回 beat_prompt

        如果用户未设置触发关键词，则对所有节拍生效。
        如果设置了关键词（逗号分隔），则仅在节拍描述/焦点命中时生效。
        """
        if not self._beat_prompt:
            return ""

        # 无触发词 = 始终生效
        if not self._beat_triggers.strip():
            return self._beat_prompt

        # 解析触发关键词
        keywords = [kw.strip() for kw in self._beat_triggers.split(",") if kw.strip()]
        if not keywords:
            return self._beat_prompt

        # 检查是否命中
        text = f"{beat_description} {beat_focus}"
        if any(kw in text for kw in keywords):
            return self._beat_prompt

        return ""

    def on_audit_enhance(
        self,
        chapter_number: int,
        chapter_content: str,
        outline: str,
    ) -> List[str]:
        """审计增强：返回用户定义的审计检查项列表"""
        return list(self._audit_checks) if self._audit_checks else []
