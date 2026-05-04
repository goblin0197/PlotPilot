"""生成结果 DTO"""
from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING
from domain.novel.value_objects.consistency_report import ConsistencyReport
from application.audit.dtos.ghost_annotation import GhostAnnotation

if TYPE_CHECKING:
    from application.audit.services.cliche_scanner import ClicheHit


@dataclass(frozen=True)
class GenerationResult:
    """章节生成结果值对象

    包含生成的内容和相关元数据
    """
    content: str
    consistency_report: ConsistencyReport
    context_used: str
    token_count: int
    ghost_annotations: List[GhostAnnotation] = None  # 幽灵批注（冲突检测结果）
    style_warnings: List['ClicheHit'] = None  # 风格警告（俗套句式检测结果）

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty")
        if self.token_count < 0:
            raise ValueError("token_count must be non-negative")
        if not self.context_used:
            raise ValueError("context_used cannot be empty")
        # 确保 ghost_annotations 不为 None
        if self.ghost_annotations is None:
            object.__setattr__(self, 'ghost_annotations', [])
        # 确保 style_warnings 不为 None
        if self.style_warnings is None:
            object.__setattr__(self, 'style_warnings', [])
