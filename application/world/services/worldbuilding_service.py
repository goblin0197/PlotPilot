"""
Service for Worldbuilding
"""
from typing import Optional
import uuid

from domain.worldbuilding.worldbuilding import Worldbuilding
from infrastructure.persistence.database.worldbuilding_repository import WorldbuildingRepository


class WorldbuildingService:
    """世界观构建服务"""

    def __init__(self, repository: WorldbuildingRepository):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - repository: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.repository = repository

    def get_worldbuilding(self, novel_id: str) -> Optional[Worldbuilding]:
        """获取小说的世界观"""
        return self.repository.get_by_novel_id(novel_id)

    def create_worldbuilding(self, novel_id: str) -> Worldbuilding:
        """创建空白世界观"""
        worldbuilding = Worldbuilding(
            id=f"wb-{uuid.uuid4().hex[:12]}",
            novel_id=novel_id,
        )
        self.repository.save(worldbuilding)
        return worldbuilding

    def update_worldbuilding(
        self,
        novel_id: str,
        core_rules: dict = None,
        geography: dict = None,
        society: dict = None,
        culture: dict = None,
        daily_life: dict = None,
    ) -> Worldbuilding:
        """更新世界观"""
        worldbuilding = self.repository.get_by_novel_id(novel_id)

        if not worldbuilding:
            worldbuilding = self.create_worldbuilding(novel_id)

        # Update core rules
        if core_rules:
            worldbuilding.power_system = core_rules.get("power_system", worldbuilding.power_system)
            worldbuilding.physics_rules = core_rules.get("physics_rules", worldbuilding.physics_rules)
            worldbuilding.magic_tech = core_rules.get("magic_tech", worldbuilding.magic_tech)

        # Update geography
        if geography:
            worldbuilding.terrain = geography.get("terrain", worldbuilding.terrain)
            worldbuilding.climate = geography.get("climate", worldbuilding.climate)
            worldbuilding.resources = geography.get("resources", worldbuilding.resources)
            worldbuilding.ecology = geography.get("ecology", worldbuilding.ecology)

        # Update society
        if society:
            worldbuilding.politics = society.get("politics", worldbuilding.politics)
            worldbuilding.economy = society.get("economy", worldbuilding.economy)
            worldbuilding.class_system = society.get("class_system", worldbuilding.class_system)

        # Update culture
        if culture:
            worldbuilding.history = culture.get("history", worldbuilding.history)
            worldbuilding.religion = culture.get("religion", worldbuilding.religion)
            worldbuilding.taboos = culture.get("taboos", worldbuilding.taboos)

        # Update daily life
        if daily_life:
            worldbuilding.food_clothing = daily_life.get("food_clothing", worldbuilding.food_clothing)
            worldbuilding.language_slang = daily_life.get("language_slang", worldbuilding.language_slang)
            worldbuilding.entertainment = daily_life.get("entertainment", worldbuilding.entertainment)

        self.repository.save(worldbuilding)
        return worldbuilding
