"""SQLite 情节弧仓储（一书多弧以 slug 区分；读写 API 默认 slug=default）。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from domain.novel.entities.plot_arc import PlotArc
from domain.novel.repositories.plot_arc_repository import PlotArcRepository
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.plot_point import PlotPoint, PlotPointType
from domain.novel.value_objects.tension_level import TensionLevel
from infrastructure.persistence.database.connection import DatabaseConnection

DEFAULT_SLUG = "default"


class SqlitePlotArcRepository(PlotArcRepository):
    """定义 `SqlitePlotArcRepository`，作为基础设施层中的仓储协作者。

    职责: 封装数据访问边界，避免上层直接依赖具体持久化细节。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    def __init__(self, db: DatabaseConnection):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - db: 数据库连接或访问封装，用于执行持久化操作。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self.db = db

    def _conn(self):
        """同步执行 `_conn` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_conn` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return self.db.get_connection()

    def _now(self) -> str:
        """同步执行 `_now` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_now` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return datetime.utcnow().isoformat()

    def save(self, plot_arc: PlotArc) -> None:
        """同步执行 `save` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `save` 这一入口。
        关键输入:
        - plot_arc: `PlotArc` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        now = self._now()
        slug = plot_arc.slug or DEFAULT_SLUG
        conn = self._conn()
        try:
            conn.execute(
                "DELETE FROM plot_arcs WHERE novel_id = ? AND slug = ?",
                (plot_arc.novel_id.value, slug),
            )
            conn.execute(
                """
                INSERT INTO plot_arcs (
                    id, novel_id, slug, display_name, extensions, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, '{}', ?, ?)
                """,
                (
                    plot_arc.id,
                    plot_arc.novel_id.value,
                    slug,
                    plot_arc.display_name or "",
                    now,
                    now,
                ),
            )
            for i, point in enumerate(sorted(plot_arc.key_points, key=lambda p: p.chapter_number)):
                pid = f"{plot_arc.id}-p-{point.chapter_number}"
                conn.execute(
                    """
                    INSERT INTO plot_points
                    (id, plot_arc_id, sort_order, chapter_number, point_type, description, tension)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pid,
                        plot_arc.id,
                        i,
                        point.chapter_number,
                        point.point_type.value,
                        point.description,
                        point.tension.value,
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def get_by_novel_id(self, novel_id: NovelId) -> Optional[PlotArc]:
        """同步读取 `by_novel_id` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_by_novel_id` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `Optional[PlotArc]`；当目标不存在、依赖不可用或条件不满足时可能返回 `None`。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one(
            """
            SELECT * FROM plot_arcs
            WHERE novel_id = ? AND slug = ?
            """,
            (novel_id.value, DEFAULT_SLUG),
        )
        if not row:
            return None
        return self._row_to_plot_arc(row, novel_id)

    def _row_to_plot_arc(self, row: dict, novel_id: NovelId) -> PlotArc:
        """同步转换或规范化 `row_plot_arc` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_row_to_plot_arc` 这一入口。
        关键输入:
        - row: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: `PlotArc`；具体语义由调用场景和返回类型共同约束。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        arc_id = row["id"]
        points = self.db.fetch_all(
            """
            SELECT chapter_number, point_type, description, tension
            FROM plot_points
            WHERE plot_arc_id = ?
            ORDER BY sort_order, chapter_number
            """,
            (arc_id,),
        )
        key_points = [
            PlotPoint(
                chapter_number=p["chapter_number"],
                point_type=PlotPointType(p["point_type"]),
                description=p["description"],
                tension=TensionLevel(int(p["tension"])),
            )
            for p in points
        ]
        slug = row.get("slug") or DEFAULT_SLUG
        display_name = row.get("display_name") or ""
        return PlotArc(
            id=arc_id,
            novel_id=novel_id,
            key_points=key_points,
            slug=slug,
            display_name=display_name,
        )

    def delete(self, novel_id: NovelId) -> None:
        """同步执行 `delete` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `delete` 这一入口。
        关键输入:
        - novel_id: 业务标识或配置键，用于定位目标记录。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 可能读取或写入 SQLite/仓储状态。
        异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
        """
        row = self.db.fetch_one(
            """
            SELECT id FROM plot_arcs
            WHERE novel_id = ? AND slug = ?
            """,
            (novel_id.value, DEFAULT_SLUG),
        )
        if not row:
            return
        conn = self._conn()
        try:
            conn.execute("DELETE FROM plot_points WHERE plot_arc_id = ?", (row["id"],))
            conn.execute("DELETE FROM plot_arcs WHERE id = ?", (row["id"],))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
