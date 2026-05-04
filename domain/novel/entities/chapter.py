# domain/novel/entities/chapter.py
from enum import Enum
from datetime import datetime
from domain.shared.base_entity import BaseEntity
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.chapter_content import ChapterContent
from domain.novel.value_objects.word_count import WordCount


class ChapterStatus(str, Enum):
    """章节状态"""
    DRAFT = "draft"
    REVIEWING = "reviewing"
    COMPLETED = "completed"


class Chapter(BaseEntity):
    """章节实体"""

    def __init__(
        self,
        id: str,
        novel_id: NovelId,
        number: int,
        title: str,
        content: str = "",
        outline: str = "",
        status: ChapterStatus = ChapterStatus.DRAFT,
        tension_score: float = 50.0,
        plot_tension: float = 50.0,
        emotional_tension: float = 50.0,
        pacing_tension: float = 50.0,
    ):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - id: 业务标识或配置键，用于定位目标记录。
        - novel_id: 业务标识或配置键，用于定位目标记录。
        - number: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        - title: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - content: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - outline: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - status: `ChapterStatus` 类型的业务输入，参与本函数的主要计算或流程控制。
        - tension_score: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        - plot_tension: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        - emotional_tension: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        - pacing_tension: `float` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        super().__init__(id)
        self.novel_id = novel_id
        self.number = number
        self.title = title
        self._content_text = content  # 直接存储文本，允许空内容
        self.outline = outline  # 章节大纲
        self.status = status
        self.tension_score = tension_score  # 章节综合张力值 0-100
        self.plot_tension = plot_tension  # 情节张力 0-100
        self.emotional_tension = emotional_tension  # 情绪张力 0-100
        self.pacing_tension = pacing_tension  # 节奏张力 0-100

    @property
    def content(self) -> str:
        """读取或计算 `content` 对应的派生值。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `content` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self._content_text

    @property
    def word_count(self) -> WordCount:
        """读取或计算 `word_count` 对应的派生值。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `word_count` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `WordCount`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if not self._content_text:
            return WordCount(0)
        content_obj = ChapterContent(self._content_text)
        return WordCount(content_obj.word_count())

    def update_content(self, content: str) -> None:
        """更新内容（允许空内容用于草稿）"""
        self._content_text = content
        self.updated_at = datetime.utcnow()

    def update_tension_score(self, score: float) -> None:
        """更新张力分数（0-100）"""
        if not 0 <= score <= 100:
            raise ValueError(f"Tension score must be between 0 and 100, got {score}")
        self.tension_score = score
        self.updated_at = datetime.utcnow()

    def update_tension_dimensions(self, dimensions: "TensionDimensions") -> None:
        """从 TensionDimensions 值对象更新全部张力字段。"""
        self.plot_tension = dimensions.plot_tension
        self.emotional_tension = dimensions.emotional_tension
        self.pacing_tension = dimensions.pacing_tension
        self.tension_score = dimensions.composite_score
        self.updated_at = datetime.utcnow()
