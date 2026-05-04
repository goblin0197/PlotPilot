"""向量检索门面，隔离异步调用"""
import asyncio
import concurrent.futures
from typing import List, Optional

from domain.ai.services.vector_store import VectorStore
from domain.ai.services.embedding_service import EmbeddingService


class VectorRetrievalFacade:
    """向量检索门面

    提供同步接口，内部使用 asyncio 隔离异步调用，避免全栈 async 改造。
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
    ):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - vector_store: `VectorStore` 类型的业务输入，参与本函数的主要计算或流程控制。
        - embedding_service: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 可能调用 LLM、向量检索或生成链路。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def sync_search(
        self,
        collection: str,
        query_text: str,
        limit: int = 5,
    ) -> List[dict]:
        """同步搜索接口

        Args:
            collection: 集合名称
            query_text: 查询文本
            limit: 返回结果数量

        Returns:
            相似向量列表，每个元素包含 id, score, payload
        """
        # 若在已有事件循环内（如 FastAPI / AutopilotDaemon asyncio.run 链），
        # run_until_complete 会报错 "This event loop is already running" 并阻塞同线程其它任务。
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._async_search(collection, query_text, limit))

        def _run_in_fresh_loop() -> List[dict]:
            """同步执行 `_run_in_fresh_loop` 对应的业务步骤。

            职责: 位于应用层，负责上述行为，并把相关输入、输出和副作用集中在 `_run_in_fresh_loop` 这一入口。
            关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
            关键输出: `List[dict]`；按调用约定排序或过滤后的结果集合。
            副作用: 会在事件循环中等待异步 I/O 或后台任务。
            异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
            """
            return asyncio.run(self._async_search(collection, query_text, limit))

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(_run_in_fresh_loop).result()

    async def _async_search(
        self,
        collection: str,
        query_text: str,
        limit: int,
    ) -> List[dict]:
        """内部异步搜索实现"""
        # 生成查询向量
        query_vector = await self.embedding_service.embed(query_text)

        # 执行向量搜索
        results = await self.vector_store.search(
            collection=collection,
            query_vector=query_vector,
            limit=limit,
        )

        return results
