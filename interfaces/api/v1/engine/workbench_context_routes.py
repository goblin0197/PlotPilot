"""工作台聚合上下文：一次 GET 对齐「故事线·弧光 / 编年史 / 叙事知识 / 关系图 / 伏笔 / 宏观 / 沙盒依赖」只读数据。"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from application.workbench.workbench_context_service import build_workbench_context_bundle
from domain.novel.repositories.plot_arc_repository import PlotArcRepository
from infrastructure.persistence.database.triple_repository import TripleRepository
from interfaces.api.dependencies import (
    get_bible_service,
    get_chapter_repository,
    get_database,
    get_foreshadowing_repository,
    get_knowledge_service,
    get_novel_service,
    get_plot_arc_repository,
    get_snapshot_service,
    get_storyline_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novels", tags=["workbench-context"])


def get_triple_repository() -> TripleRepository:
    """同步读取 `triple_repository` 相关的数据或状态。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `get_triple_repository` 这一入口。
    关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
    关键输出: `TripleRepository`；具体语义由调用场景和返回类型共同约束。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    return TripleRepository()


@router.get("/{novel_id}/workbench-context")
async def get_workbench_context(
    novel_id: str,
    novel_service=Depends(get_novel_service),
    bible_service=Depends(get_bible_service),
    chapter_repo=Depends(get_chapter_repository),
    snapshot_service=Depends(get_snapshot_service),
    storyline_manager=Depends(get_storyline_manager),
    plot_arc_repo: PlotArcRepository = Depends(get_plot_arc_repository),
    knowledge_service=Depends(get_knowledge_service),
    foreshadowing_repo=Depends(get_foreshadowing_repository),
    triple_repository: TripleRepository = Depends(get_triple_repository),
    db=Depends(get_database),
) -> Dict[str, Any]:
    """单次拉取多域数据，与各子路由使用相同仓储逻辑；前端可替代多次并行 GET。"""
    bundle = await build_workbench_context_bundle(
        novel_id,
        novel_service=novel_service,
        bible_service=bible_service,
        chapter_repo=chapter_repo,
        snapshot_service=snapshot_service,
        storyline_manager=storyline_manager,
        plot_arc_repo=plot_arc_repo,
        knowledge_service=knowledge_service,
        foreshadowing_repo=foreshadowing_repo,
        triple_repository=triple_repository,
        db_connection=db,
    )
    if bundle.get("error") == "novel_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    return bundle
