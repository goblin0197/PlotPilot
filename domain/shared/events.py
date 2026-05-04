# domain/shared/events.py
from datetime import datetime
from typing import Any, Dict
import uuid


class DomainEvent:
    """领域事件基类"""

    def __init__(self, aggregate_id: str):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - aggregate_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.event_id = str(uuid.uuid4())
        self.aggregate_id = aggregate_id
        self.occurred_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "event_id": self.event_id,
            "aggregate_id": self.aggregate_id,
            "occurred_at": self.occurred_at.isoformat(),
            "event_type": self.__class__.__name__
        }
