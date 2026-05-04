"""双螺旋编年史 BFF：剧情时间线（Bible）× 语义快照（novel_snapshots）按 chapter_index 拉链聚合。"""
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from application.codex.chronicles_service import build_chronicles_rows
from application.world.services.bible_service import BibleService
from application.snapshot.services.snapshot_service import SnapshotService
from domain.novel.value_objects.novel_id import NovelId
from interfaces.api.dependencies import (
    get_bible_service,
    get_chapter_repository,
    get_novel_service,
    get_snapshot_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novels", tags=["chronicles"])


class StoryEventItem(BaseModel):
    """定义 `StoryEventItem`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    note_id: str
    time: str
    title: str
    description: str
    source_chapter: Optional[int] = None


class SnapshotItem(BaseModel):
    """定义 `SnapshotItem`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    id: str
    kind: str = Field(..., description="AUTO / MANUAL")
    name: str
    branch_name: str = "main"
    created_at: Optional[str] = None
    description: Optional[str] = None
    anchor_chapter: Optional[int] = None


class ChronicleRow(BaseModel):
    """定义 `ChronicleRow`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    chapter_index: int
    story_events: List[StoryEventItem] = Field(default_factory=list)
    snapshots: List[SnapshotItem] = Field(default_factory=list)


class ChroniclesResponse(BaseModel):
    """定义 `ChroniclesResponse`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    rows: List[ChronicleRow]
    max_chapter_in_book: int
    note: str = (
        "剧情节点来自 Bible.timeline_notes；快照来自 novel_snapshots。"
        "chapter_index 由「第N章」文案或快照内章节指针推断。"
    )


@router.get("/{novel_id}/chronicles", response_model=ChroniclesResponse)
async def get_chronicles(
    novel_id: str,
    novel_service=Depends(get_novel_service),
    bible_service: BibleService = Depends(get_bible_service),
    chapter_repo=Depends(get_chapter_repository),
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
) -> ChroniclesResponse:
    """异步读取 `chronicles` 相关的数据或状态。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `get_chronicles` 这一入口。
    关键输入:
    - novel_id: 业务标识或配置键，用于定位目标记录。
    - novel_service: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
    - bible_service: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
    - chapter_repo: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
    - snapshot_service: 外部协作者实例，负责仓储、服务编排或第三方能力适配。
    关键输出: `ChroniclesResponse`；具体语义由调用场景和返回类型共同约束。
    副作用: 会在事件循环中等待异步 I/O 或后台任务。
    异常/边界: 会显式抛出 `HTTPException`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
    """
    if novel_service.get_novel(novel_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")

    bible = bible_service.get_bible_by_novel(novel_id)
    notes_tuples: List[tuple] = []
    if bible and bible.timeline_notes:
        for n in bible.timeline_notes:
            notes_tuples.append((n.id, n.time_point or "", n.event or "", n.description or ""))

    chapters = chapter_repo.list_by_novel(NovelId(novel_id))
    id_to_number = {c.id: c.number for c in chapters}
    max_ch = max((c.number for c in chapters), default=1)

    try:
        snapshots_raw: List[Dict[str, Any]] = snapshot_service.list_snapshots_with_pointers(novel_id)
    except sqlite3.OperationalError as e:
        logger.warning("chronicles: novel_snapshots unreadable: %s", e)
        snapshots_raw = []

    raw_rows = build_chronicles_rows(notes_tuples, snapshots_raw, id_to_number)

    rows: List[ChronicleRow] = []
    for r in raw_rows:
        rows.append(
            ChronicleRow(
                chapter_index=r["chapter_index"],
                story_events=[StoryEventItem(**x) for x in r["story_events"]],
                snapshots=[SnapshotItem(**x) for x in r["snapshots"]],
            )
        )

    return ChroniclesResponse(rows=rows, max_chapter_in_book=max_ch)
