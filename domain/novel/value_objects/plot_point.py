from dataclasses import dataclass
from enum import Enum
from domain.novel.value_objects.tension_level import TensionLevel


class PlotPointType(str, Enum):
    """剧情点类型"""
    OPENING = "opening"              # 开端
    RISING_ACTION = "rising"         # 上升
    TURNING_POINT = "turning"        # 转折
    CLIMAX = "climax"                # 高潮
    FALLING_ACTION = "falling"       # 下降
    RESOLUTION = "resolution"        # 结局


@dataclass(frozen=True)
class PlotPoint:
    """剧情点值对象"""
    chapter_number: int
    point_type: PlotPointType
    description: str
    tension: TensionLevel

    def __post_init__(self):
        """同步执行 `__post_init__` 对应的业务步骤。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__post_init__` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        if self.chapter_number < 1:
            raise ValueError("Chapter number must be >= 1")
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")
