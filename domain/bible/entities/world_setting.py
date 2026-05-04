from domain.shared.base_entity import BaseEntity


class WorldSetting(BaseEntity):
    """世界设定实体"""

    VALID_TYPES = {"location", "item", "rule"}

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        setting_type: str  # "location", "item", "rule"
    ):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于领域层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - id: 业务标识或配置键，用于定位目标记录。
        - name: 业务标识或配置键，用于定位目标记录。
        - description: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        - setting_type: `str` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 会显式抛出 `ValueError`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
        """
        super().__init__(id)

        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        if setting_type not in self.VALID_TYPES:
            raise ValueError(f"Setting type must be one of {self.VALID_TYPES}")

        self.name = name
        self.description = description
        self.setting_type = setting_type

    def update_description(self, description: str) -> None:
        """更新描述"""
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        self.description = description
