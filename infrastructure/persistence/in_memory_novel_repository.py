"""内存版小说仓储实现（用于测试守护进程）

注意：这是临时实现，生产环境需要替换为真正的数据库实现
"""
from typing import List, Optional, Dict
from domain.novel.entities.novel import Novel, AutopilotStatus
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.repositories.novel_repository import NovelRepository


class InMemoryNovelRepository(NovelRepository):
    """内存版小说仓储（用于测试）"""

    def __init__(self):
        """初始化 `InMemoryNovelRepository` 实例并注入运行所需的依赖与初始状态。

        调用方传入的协作者会被保存到实例上，后续方法复用这些依赖完成业务流程。

        返回: 无；初始化完成后状态保存在当前实例上。

        副作用: 不主动改变外部状态，除非传入对象本身在处理过程中被更新。
        """
        self._storage: Dict[str, Novel] = {}

    def save(self, novel: Novel) -> None:
        """保存小说"""
        self._storage[novel.novel_id.value] = novel

    async def async_save(self, novel: Novel) -> None:
        """异步保存小说"""
        self.save(novel)

    def get_by_id(self, novel_id: NovelId) -> Optional[Novel]:
        """根据 ID 获取小说"""
        return self._storage.get(novel_id.value)

    def list_all(self) -> List[Novel]:
        """列出所有小说"""
        return list(self._storage.values())

    def find_by_autopilot_status(self, status: AutopilotStatus) -> List[Novel]:
        """根据自动驾驶状态查询小说"""
        return [
            novel for novel in self._storage.values()
            if novel.autopilot_status == status
        ]

    def delete(self, novel_id: NovelId) -> None:
        """删除小说"""
        if novel_id.value in self._storage:
            del self._storage[novel_id.value]

    def exists(self, novel_id: NovelId) -> bool:
        """检查小说是否存在"""
        return novel_id.value in self._storage
