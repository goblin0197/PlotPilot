"""轻量级网络搜索工具，供 Agent 查证资料使用。"""
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

try:
    from ddgs import DDGS
    _DDGS_AVAILABLE = True
except ImportError:
    _DDGS_AVAILABLE = False
    logger.warning("duckduckgo-search 未安装，WebSearchTool 不可用。运行: pip install duckduckgo-search")


class WebSearchTool:
    """轻量级的网络搜索工具，供 Agent 验证资料使用"""

    @staticmethod
    def available() -> bool:
        """同步执行 `available` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `available` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 布尔值，表示判断、校验或执行条件是否成立。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return _DDGS_AVAILABLE

    @staticmethod
    def search(query: str, max_results: int = 5) -> str:
        """执行网络搜索并返回格式化结果文本"""
        if not _DDGS_AVAILABLE:
            return "搜索工具不可用（未安装 duckduckgo-search）。"

        start = time.time()
        logger.info(f"Executing web search for: '{query}'")
        try:
            results: list[dict] = []
            with DDGS(timeout=8) as ddgs:
                for r in ddgs.text(query, region='wt-wt', max_results=max_results):
                    if isinstance(r, dict):
                        results.append(
                            {
                                "title": r.get("title", "") or "",
                                "href": r.get("href", "") or "",
                                "body": r.get("body", "") or "",
                            }
                        )

            parts: list[str] = []
            for r in results:
                title = r.get("title", "")
                href = r.get("href", "")
                body = r.get("body", "")
                if href:
                    parts.append(f"【{title}】\nURL: {href}\n{body}")
                else:
                    parts.append(f"【{title}】\n{body}")

            logger.info(
                f"Web search done for: '{query}', results={len(results)}, "
                f"elapsed={time.time() - start:.2f}s"
            )
            return "\n\n".join(parts)
        except Exception as e:
            logger.error(
                f"Web search failed for query '{query}' "
                f"(elapsed={time.time() - start:.2f}s): {e}"
            )
            return f"搜索失败（{e}）。"

    @staticmethod
    def search_raw(query: str, max_results: int = 5) -> list[dict]:
        """执行网络搜索并返回原始结果列表"""
        start = time.time()
        logger.info(f"Executing web search(raw) for: '{query}'")
        try:
            results: list[dict] = []
            with DDGS(timeout=8) as ddgs:
                for r in ddgs.text(query, region='wt-wt', max_results=max_results):
                    if isinstance(r, dict):
                        results.append(
                            {
                                "title": r.get("title", "") or "",
                                "href": r.get("href", "") or "",
                                "body": r.get("body", "") or "",
                            }
                        )
            logger.info(
                f"Web search(raw) done for: '{query}', results={len(results)}, "
                f"elapsed={time.time() - start:.2f}s"
            )
            return results
        except Exception as e:
            logger.error(
                f"Web search(raw) failed for query '{query}' "
                f"(elapsed={time.time() - start:.2f}s): {e}"
            )
            return []
