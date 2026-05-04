# domain/shared/exceptions.py
class DomainException(Exception):
    """领域异常基类"""
    pass


class EntityNotFoundError(DomainException):
    """实体未找到"""
    def __init__(self, entity_type: str, entity_id: str):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - entity_type: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - entity_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class InvalidOperationError(DomainException):
    """无效操作"""
    pass


class ValidationError(DomainException):
    """验证错误"""
    pass
