"""语义快照：回滚等到位后的 HTTP 接口。"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from application.snapshot.services.snapshot_service import SnapshotService
from interfaces.api.dependencies import get_novel_service, get_snapshot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novels", tags=["snapshots"])


class SnapshotRollbackResponse(BaseModel):
    """定义 `SnapshotRollbackResponse`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    deleted_chapter_ids: List[str] = Field(default_factory=list)
    deleted_count: int = 0


@router.post(
    "/{novel_id}/snapshots/{snapshot_id}/rollback",
    response_model=SnapshotRollbackResponse,
)
async def rollback_to_snapshot(
    novel_id: str,
    snapshot_id: str,
    novel_service=Depends(get_novel_service),
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
) -> SnapshotRollbackResponse:
    """将作品章节集合恢复为快照中记录的章节指针（删除快照未包含的章节正文行）。"""
    if novel_service.get_novel(novel_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")

    try:
        result = snapshot_service.rollback_to_snapshot(novel_id, snapshot_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return SnapshotRollbackResponse(
        deleted_chapter_ids=result["deleted_chapter_ids"],
        deleted_count=result["deleted_count"],
    )
