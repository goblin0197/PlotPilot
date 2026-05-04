"""PromptManager — 提示词统一管理服务（数据库驱动版）。

核心设计：
- 提示词存入 SQLite（prompt_templates / prompt_nodes / prompt_versions）
- 单节点版本管理（每次编辑创建新版本，支持回滚）
- 整体模板概念（template 包含多个 node，可组合成工作流）
- 内置种子从 prompts_defaults.json 初始化
- Jinja2 兼容的变量渲染

数据模型：
  prompt_templates (1) ──→ (N) prompt_nodes (1) ──→ (N) prompt_versions
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 内置种子 JSON 路径
_DEFAULT_SEED_PATH = (
    Path(__file__).resolve().parent / "prompts" / "prompts_defaults.json"
)

# 分类定义（与 prompts_defaults.json 的 categories 对应）
BUILTIN_CATEGORIES = [
    {"key": "generation", "name": "📝 内容生成", "icon": "✍️",
     "description": "章节正文、场景、对白等创作类提示词", "color": "#4f46e5"},
    {"key": "extraction", "name": "🔍 信息提取", "icon": "🔎",
     "description": "从文本中提取结构化信息的分析类提示词", "color": "#0891b2"},
    {"key": "review", "name": "✅ 审稿质检", "icon": "🔬",
     "description": "一致性检查、质量评估等审稿类提示词", "color": "#b45309"},
    {"key": "planning", "name": "📐 规划设计", "icon": "📋",
     "description": "大纲拆解、节拍表、摘要、宏观规划等", "color": "#6d28d9"},
    {"key": "world", "name": "🌍 世界设定", "icon": "🏰",
     "description": "Bible 人物、地点、世界观、文风生成", "color": "#15803d"},
    {"key": "creative", "name": "🎭 创意辅助", "icon": "💡",
     "description": "对白润色、重构提案、卡文诊断等", "color": "#be185d"},
]


def _uid() -> str:
    """生成短 UUID。"""
    return uuid.uuid4().hex[:12]


class VersionInfo:
    """单个版本信息。"""

    __slots__ = ("id", "version_number", "system_prompt", "user_template",
                 "change_summary", "created_by", "created_at")

    def __init__(self, row: Optional[Dict[str, Any]] = None):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - row: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if row:
            self.id: str = row["id"]
            self.version_number: int = row["version_number"]
            self.system_prompt: str = row["system_prompt"] or ""
            self.user_template: str = row["user_template"] or ""
            self.change_summary: str = row["change_summary"] or ""
            self.created_by: str = row["created_by"] or "system"
            self.created_at: str = row["created_at"] or ""
        else:
            self.id = ""
            self.version_number = 0
            self.system_prompt = ""
            self.user_template = ""
            self.change_summary = ""
            self.created_by = "system"
            self.created_at = ""

    def to_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "id": self.id,
            "version_number": self.version_number,
            "change_summary": self.change_summary,
            "created_by": self.created_by,
            "created_at": self.created_at,
            # 预览截断
            "system_preview": self._preview(self.system_prompt, 150),
            "user_preview": self._preview(self.user_template, 150),
        }

    def to_detail_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `detail_dict` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `to_detail_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        d = self.to_dict()
        d["system_prompt"] = self.system_prompt
        d["user_template"] = self.user_template
        return d

    @staticmethod
    def _preview(text: str, max_len: int) -> str:
        """同步执行 `_preview` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_preview` 这一入口。
        关键输入:
        - text: 文本或提示词内容，是生成、解析或展示逻辑的主要输入。
        - max_len: `int` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if not text or len(text) <= max_len:
            return text or ""
        return text[:max_len] + "... (共 {} 字)".format(len(text))


class NodeInfo:
    """提示词节点信息（含当前激活版本）。"""

    __slots__ = (
        "id", "node_key", "name", "description", "category", "source",
        "output_format", "contract_module", "contract_model",
        "tags", "variables", "system_file", "is_builtin", "sort_order",
        "template_id", "active_version_id", "version_count",
        "_active_version",
    )

    def __init__(self, row: Optional[Dict[str, Any]] = None):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - row: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if row:
            self.id: str = row["id"]
            self.node_key: str = row["node_key"]
            self.name: str = row["name"]
            self.description: str = row["description"] or ""
            self.category: str = row["category"] or "generation"
            self.source: str = row["source"] or ""
            self.output_format: str = row["output_format"] or "text"
            self.contract_module: Optional[str] = row.get("contract_module")
            self.contract_model: Optional[str] = row.get("contract_model")
            self.tags: List[str] = self._parse_json_list(row.get("tags"))
            self.variables: List[Dict[str, Any]] = self._parse_json(
                row.get("variables"), []
            )
            self.system_file: Optional[str] = row.get("system_file")
            self.is_builtin: bool = bool(row.get("is_builtin", 0))
            self.sort_order: int = row.get("sort_order", 0)
            self.template_id: str = row["template_id"]
            self.active_version_id: Optional[str] = row.get("active_version_id")
            self.version_count: int = row.get("version_count", 0)
        else:
            self.id = _uid()
            self.node_key = ""
            self.name = ""
            self.description = ""
            self.category = "generation"
            self.source = ""
            self.output_format = "text"
            self.contract_module = None
            self.contract_model = None
            self.tags = []
            self.variables = []
            self.system_file = None
            self.is_builtin = False
            self.sort_order = 0
            self.template_id = ""
            self.active_version_id = None
            self.version_count = 0
        self._active_version: Optional[VersionInfo] = None

    @staticmethod
    def _parse_json(val: Any, default=None):
        """同步执行 `_parse_json` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_parse_json` 这一入口。
        关键输入:
        - val: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
        - default: 目标值缺失时使用的回退值。
        关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if val is None:
            return default
        if isinstance(val, (list, dict)):
            return val
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def _parse_json_list(val: Any) -> List[str]:
        """同步执行 `_parse_json_list` 对应的业务步骤。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `_parse_json_list` 这一入口。
        关键输入:
        - val: `Any` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: `List[str]`；按调用约定排序或过滤后的结果集合。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        result = NodeInfo._parse_json(val, [])
        if isinstance(result, list):
            return [str(x) for x in result]
        return []

    def set_active_version(self, version: VersionInfo) -> None:
        """同步写入、更新或清理 `active_version` 相关状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `set_active_version` 这一入口。
        关键输入:
        - version: `VersionInfo` 类型的业务输入，参与本函数的主要计算或流程控制。
        关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        self._active_version = version

    def get_active_system(self) -> str:
        """同步读取 `active_system` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_active_system` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if self._active_version:
            return self._active_version.system_prompt
        return ""

    def get_active_user_template(self) -> str:
        """同步读取 `active_user_template` 相关的数据或状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `get_active_user_template` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `str`；具体语义由调用场景和返回类型共同约束。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if self._active_version:
            return self._active_version.user_template
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        av = self._active_version
        return {
            "id": self.id,
            "node_key": self.node_key,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "source": self.source,
            "output_format": self.output_format,
            "contract_module": self.contract_module,
            "contract_model": self.contract_model,
            "tags": self.tags,
            "variables": self.variables,
            "variable_names": [v.get("name", "") for v in self.variables],
            "system_file": self.system_file,
            "is_builtin": self.is_builtin,
            "sort_order": self.sort_order,
            "template_id": self.template_id,
            "version_count": self.version_count,
            # 当前激活版本的预览
            "system_preview": av.system_prompt[:200] + "..." if av and len(av.system_prompt) > 200 else (av.system_prompt or ""),
            "user_template_preview": av.user_template[:200] + "..." if av and len(av.user_template) > 200 else (av.user_template or ""),
            "has_user_edit": av.created_by == "user" if av else False,
        }

    def to_detail_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `detail_dict` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `to_detail_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        d = self.to_dict()
        d["system"] = self.get_active_system()
        d["user_template"] = self.get_active_user_template()
        return d


class TemplateInfo:
    """模板包信息。"""

    __slots__ = ("id", "name", "description", "category", "version",
                 "author", "icon", "color", "is_builtin", "metadata",
                 "node_count")

    def __init__(self, row: Optional[Dict[str, Any]] = None):
        """初始化当前实例，接收依赖与初始配置并保存为后续方法可复用的状态。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__init__` 这一入口。
        关键输入:
        - row: 结构化数据载荷，通常来自请求、数据库行或上游服务。
        关键输出: 无返回值；初始化结果体现在当前实例的字段状态上。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        if row:
            self.id: str = row["id"]
            self.name: str = row["name"]
            self.description: str = row["description"] or ""
            self.category: str = row["category"] or "user"
            self.version: str = row["version"] or "1.0.0"
            self.author: str = row["author"] or ""
            self.icon: str = row["icon"] or "📦"
            self.color: str = row["color"] or "#6b7280"
            self.is_builtin: bool = bool(row.get("is_builtin", 0))
            self.metadata: Dict[str, Any] = {}
            raw_meta = row.get("metadata")
            if raw_meta:
                try:
                    self.metadata = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
                except (json.JSONDecodeError, TypeError):
                    pass
            self.node_count: int = row.get("node_count", 0)
        else:
            self.id = _uid()
            self.name = ""
            self.description = ""
            self.category = "user"
            self.version = "1.0.0"
            self.author = ""
            self.icon = "📦"
            self.color = "#6b7280"
            self.is_builtin = False
            self.metadata = {}
            self.node_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """同步转换或规范化 `dict` 相关的数据结构。

        职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `to_dict` 这一入口。
        关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
        关键输出: `Dict[str, Any]`；包含后续流程所需字段的结构化映射。
        副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
        异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "author": self.author,
            "icon": self.icon,
            "color": self.color,
            "is_builtin": self.is_builtin,
            "metadata": self.metadata,
            "node_count": self.node_count,
        }


class PromptManager:
    """提示词管理器 — 数据库驱动版。

    职责：
    1. 从 DB 加载/查询提示词（nodes + versions）
    2. 版本管理：每次编辑 → 新建版本；支持回滚到历史版本
    3. 模板包管理：一组相关节点的集合
    4. 内置种子初始化：首次启动时从 prompts_defaults.json 导入
    5. 变量渲染：{variable} 占位符替换
    """

    def __init__(self, db_connection=None):
        """
        Args:
            db_connection: DatabaseConnection 实例（延迟注入，避免循环导入）。
                           为 None 时使用全局 get_database()（与 FastAPI / paths.DATA_DIR 一致）。
        """
        self._db = db_connection
        self._seeded = False

    def _get_db(self):
        """与主应用共用同一 SQLite（含桌面版 AITEXT_PROD_DATA_DIR）。"""
        if self._db is not None:
            return self._db
        from infrastructure.persistence.database.connection import get_database

        return get_database()

    # ------------------------------------------------------------------
    # 种子初始化
    # ------------------------------------------------------------------

    def ensure_seeded(self) -> bool:
        """确保内置种子已导入数据库（幂等）。"""
        if self._seeded:
            return True
        db = self._get_db()
        conn = db.get_connection()

        # 检查是否已有内置模板包
        row = conn.execute(
            "SELECT id FROM prompt_templates WHERE is_builtin=1 LIMIT 1"
        ).fetchone()
        if row:
            self._seeded = True
            logger.info("PromptManager: 内置种子已存在，跳过初始化")
            return True

        seed_path = _DEFAULT_SEED_PATH
        if not seed_path.exists():
            logger.warning("内置种子文件不存在: %s", seed_path)
            return False

        try:
            seed_data = json.loads(seed_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("读取种子文件失败: %s", exc)
            return False

        template_id = _uid()
        now = datetime.now().isoformat()

        # 创建内置模板包
        meta = seed_data.get("_meta", {})
        conn.execute("""
            INSERT INTO prompt_templates
            (id, name, description, category, version, author, icon, color, is_builtin, metadata, created_at, updated_at)
            VALUES (?, ?, ?, 'builtin', ?, ?, '🏗️', '#4f46e5', 1, ?, ?, ?)
        """, (
            template_id,
            meta.get("name", "PlotPilot 内置"),
            meta.get("description", ""),
            meta.get("version", "1.0.0"),
            meta.get("author", "PlotPilot Team"),
            json.dumps(meta, ensure_ascii=False),
            now, now,
        ))

        # 批量插入节点和初始版本
        prompts = seed_data.get("prompts", [])
        for idx, p in enumerate(prompts):
            node_id = _uid()
            ver_id = _uid()
            tags_json = json.dumps(p.get("tags", []), ensure_ascii=False)
            vars_json = json.dumps(p.get("variables", []), ensure_ascii=False)

            conn.execute("""
                INSERT INTO prompt_nodes
                (id, template_id, node_key, name, description, category, source,
                 output_format, contract_module, contract_model, tags, variables,
                 system_file, is_builtin, sort_order, active_version_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """, (
                node_id, template_id,
                p.get("id", f"node-{idx}"),
                p.get("name", ""),
                p.get("description", ""),
                p.get("category", "generation"),
                p.get("source", ""),
                p.get("output_format", "text"),
                p.get("contract_module"),
                p.get("contract_model"),
                tags_json, vars_json,
                p.get("system_file"),
                idx,
                ver_id, now, now,
            ))

            system_content = p.get("system", "")

            conn.execute("""
                INSERT INTO prompt_versions
                (id, node_id, version_number, system_prompt, user_template,
                 change_summary, created_by, created_at)
                VALUES (?, ?, 1, ?, ?, '初始种子', 'system', ?)
            """, (ver_id, node_id, system_content, p.get("user_template", ""), now))

        conn.commit()
        self._seeded = True
        count = len(prompts)
        logger.info("PromptManager: 已导入 %d 个内置提示词种子", count)
        return True

    # ------------------------------------------------------------------
    # 模板包 CRUD
    # ------------------------------------------------------------------

    def list_templates(self) -> List[TemplateInfo]:
        """列出所有模板包。"""
        db = self._get_db()
        rows = db.execute("""
            SELECT t.*, COUNT(n.id) AS node_count
            FROM prompt_templates t
            LEFT JOIN prompt_nodes n ON n.template_id = t.id
            GROUP BY t.id
            ORDER BY t.is_builtin DESC, t.created_at ASC
        """).fetchall()
        return [TemplateInfo(dict(r)) for r in rows]

    def get_template(self, template_id: str) -> Optional[TemplateInfo]:
        """获取单个模板包详情。"""
        db = self._get_db()
        row = db.execute("""
            SELECT t.*, COUNT(n.id) AS node_count
            FROM prompt_templates t
            LEFT JOIN prompt_nodes n ON n.template_id = t.id
            WHERE t.id = ?
            GROUP BY t.id
        """, (template_id,)).fetchone()
        return TemplateInfo(dict(row)) if row else None

    def create_template(self, name: str, description:
        str = "",
                        category: str = "user", **kwargs) -> TemplateInfo:
        """创建自定义模板包。"""
        db = self._get_db()
        tid = _uid()
        now = datetime.now().isoformat()
        conn = db.get_connection()
        conn.execute("""
            INSERT INTO prompt_templates
            (id, name, description, category, version, author, icon, color,
             is_builtin, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, '1.0.0', '', '📦', '#6b7280', 0, '{}', ?, ?)
        """, (tid, name, description, category, now, now))
        conn.commit()
        return TemplateInfo({"id": tid, "name": name, "description": description,
                             "category": category, "node_count": 0})

    # ------------------------------------------------------------------
    # 节点 CRUD
    # ------------------------------------------------------------------

    def list_nodes(
        self,
        category: Optional[str] = None,
        template_id: Optional[str] = None,
        include_versions: bool = False,
    ) -> List[NodeInfo]:
        """列举提示词节点，可按分类/模板过滤。"""
        db = self._get_db()
        params: List[Any] = []
        where_clauses = ["1=1"]

        if category:
            where_clauses.append("n.category = ?")
            params.append(category)
        if template_id:
            where_clauses.append("n.template_id = ?")
            params.append(template_id)

        where_sql = " AND ".join(where_clauses)

        rows = db.execute(f"""
            SELECT n.*, COUNT(v.id) AS version_count
            FROM prompt_nodes n
            LEFT JOIN prompt_versions v ON v.node_id = n.id
            WHERE {where_sql}
            GROUP BY n.id
            ORDER BY n.sort_order ASC, n.node_key ASC
        """, params).fetchall()

        nodes = [NodeInfo(dict(r)) for r in rows]

        if include_versions:
            self._attach_active_versions(nodes)

        return nodes

    def get_node(self, node_key_or_id:
        str,
                 by_key: bool = True) -> Optional[NodeInfo]:
        """获取单个节点详情（含激活版本内容）。"""
        db = self._get_db()
        if by_key:
            col = "node_key"
        else:
            col = "id"

        row = db.execute(f"""
            SELECT n.*, COUNT(v.id) AS version_count
            FROM prompt_nodes n
            LEFT JOIN prompt_versions v ON v.node_id = n.id
            WHERE n.{col} = ?
            GROUP BY n.id
        """, (node_key_or_id,)).fetchone()

        if not row:
            return None

        node = NodeInfo(dict(row))
        self._attach_active_versions([node])
        return node

    def search_nodes(self, query: str) -> List[NodeInfo]:
        """搜索节点（匹配 name/description/tags/source/node_key）。"""
        q = query.lower().strip()
        if not q:
            return self.list_nodes(include_versions=True)

        db = self._get_db()
        pattern = f"%{q}%"
        rows = db.execute("""
            SELECT n.*, COUNT(v.id) AS version_count
            FROM prompt_nodes n
            LEFT JOIN prompt_versions v ON v.node_id = n.id
            WHERE LOWER(n.name) LIKE ? OR LOWER(n.description) LIKE ?
               OR LOWER(n.source) LIKE ? OR LOWER(n.node_key) LIKE ?
               OR n.tags LIKE ?
            GROUP BY n.id
            ORDER BY n.sort_order ASC
        """, (pattern, pattern, pattern, pattern, pattern)).fetchall()

        nodes = [NodeInfo(dict(r)) for r in rows]
        self._attach_active_versions(nodes)
        return nodes

    def create_node(self, template_id: str, node_key: str, name:
        str,
                    system_prompt: str = "", user_template: str = "",
                    **kwargs) -> NodeInfo:
        """在指定模板包下创建新节点（v1）。"""
        db = self._get_db()
        node_id = _uid()
        ver_id = _uid()
        now = datetime.now().isoformat()

        tags_s = json.dumps(kwargs.get("tags", []), ensure_ascii=False)
        vars_s = json.dumps(kwargs.get("variables", []), ensure_ascii=False)
        out_fmt = kwargs.get("output_format") or "text"
        src = kwargs.get("source") or ""
        cm = kwargs.get("contract_module")
        cmodel = kwargs.get("contract_model")

        db.execute("""
            INSERT INTO prompt_nodes
            (id, template_id, node_key, name, description, category,
             source, output_format, contract_module, contract_model, tags, variables,
             is_builtin, sort_order, active_version_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
        """, (
            node_id, template_id, node_key, name,
            kwargs.get("description", ""), kwargs.get("category", "generation"),
            src, out_fmt, cm, cmodel, tags_s, vars_s,
            ver_id, now, now,
        ))

        db.execute("""
            INSERT INTO prompt_versions
            (id, node_id, version_number, system_prompt, user_template,
             change_summary, created_by, created_at)
            VALUES (?, ?, 1, ?, ?, '初始版本', 'user', ?)
        """, (ver_id, node_id, system_prompt, user_template, now))

        db.commit()
        return self.get_node(node_id, by_key=False)

    def delete_node(self, node_id: str) -> bool:
        """删除节点及其所有版本。"""
        db = self._get_db()
        cursor = db.execute("DELETE FROM prompt_nodes WHERE id = ?", (node_id,))
        db.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # 版本管理（核心！）
    # ------------------------------------------------------------------

    def get_node_versions(self, node_id: str) -> List[VersionInfo]:
        """获取节点的所有版本列表（时间线）。"""
        db = self._get_db()
        rows = db.execute("""
            SELECT * FROM prompt_versions
            WHERE node_id = ?
            ORDER BY version_number DESC
        """, (node_id,)).fetchall()
        return [VersionInfo(dict(r)) for r in rows]

    def get_version(self, version_id: str) -> Optional[VersionInfo]:
        """获取单个版本详情。"""
        db = self._get_db()
        row = db.execute(
            "SELECT * FROM prompt_versions WHERE id = ?", (version_id,)
        ).fetchone()
        return VersionInfo(dict(row)) if row else None

    def update_node(
        self,
        node_id: str,
        system_prompt: Optional[str] = None,
        user_template: Optional[str] = None,
        change_summary: str = "",
        **kwargs,
    ) -> Optional[NodeInfo]:
        """更新节点内容 —— 自动创建新版本（不覆盖旧版）。

        Returns:
            更新后的节点（含新激活版本）。
        """
        db = self._get_db()

        # 获取当前最新版本号
        row = db.execute(
            "SELECT COALESCE(MAX(version_number), 0) AS max_ver "
            "FROM prompt_versions WHERE node_id = ?",
            (node_id,),
        ).fetchone()
        next_ver = (row["max_ver"] if row else 0) + 1
        new_ver_id = _uid()
        now = datetime.now().isoformat()

        # 获取当前版本作为基础
        current = self._get_current_version(db, node_id)
        new_system = system_prompt if system_prompt is not None else (
            current.system_prompt if current else ""
        )
        new_user = user_template if user_template is not None else (
            current.user_template if current else ""
        )

        # 创建新版本
        db.execute("""
            INSERT INTO prompt_versions
            (id, node_id, version_number, system_prompt, user_template,
             change_summary, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'user', ?)
        """, (new_ver_id, node_id, next_ver, new_system, new_user,
              change_summary or f"v{next_ver} 编辑", now))

        # 更新节点的 active_version_id 和元字段
        set_clauses = ["active_version_id = ?", "updated_at = ?"]
        params: List[Any] = [new_ver_id, now]

        if kwargs.get("name"):
            set_clauses.append("name = ?")
            params.append(kwargs["name"])
        if kwargs.get("description") is not None:
            set_clauses.append("description = ?")
            params.append(kwargs["description"])
        if kwargs.get("tags") is not None:
            set_clauses.append("tags = ?")
            params.append(json.dumps(kwargs["tags"], ensure_ascii=False))
        if kwargs.get("variables") is not None:
            set_clauses.append("variables = ?")
            params.append(json.dumps(kwargs["variables"], ensure_ascii=False))
        if kwargs.get("output_format") is not None:
            set_clauses.append("output_format = ?")
            params.append(kwargs["output_format"])
        if kwargs.get("contract_module") is not None:
            set_clauses.append("contract_module = ?")
            params.append(kwargs["contract_module"])
        if kwargs.get("contract_model") is not None:
            set_clauses.append("contract_model = ?")
            params.append(kwargs["contract_model"])
        if kwargs.get("source") is not None:
            set_clauses.append("source = ?")
            params.append(kwargs["source"])
        if kwargs.get("category") is not None:
            set_clauses.append("category = ?")
            params.append(kwargs["category"])

        params.append(node_id)
        sql = f"UPDATE prompt_nodes SET {', '.join(set_clauses)} WHERE id = ?"
        db.execute(sql, params)
        db.commit()

        return self.get_node(node_id, by_key=False)

    def rollback_node(self, node_id:
        str,
                      target_version_id: str) -> Optional[NodeInfo]:
        """回滚节点到指定历史版本（创建一个新版本作为「回滚快照」）。

        这样做的好处：
        - 不删除任何历史记录
        - 回滚本身也是一个版本，可以再次回滚回来
        """
        db = self._get_db()

        # 获取目标版本
        target = self.get_version(target_version_id)
        if not target:
            return None

        # 获取当前最新版本号
        row = db.execute(
            "SELECT COALESCE(MAX(version_number), 0) AS max_ver "
            "FROM prompt_versions WHERE node_id = ?",
            (node_id,),
        ).fetchone()
        next_ver = (row["max_ver"] if row else 0) + 1
        new_ver_id = _uid()
        now = datetime.now().isoformat()

        # 以目标版本的内容创建新版本（标记为回滚）
        db.execute("""
            INSERT INTO prompt_versions
            (id, node_id, version_number, system_prompt, user_template,
             change_summary, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'user', ?)
        """, (
            new_ver_id, node_id, next_ver,
            target.system_prompt, target.user_template,
            f"回滚到 v{target.version_number}",
            now,
        ))

        db.execute(
            "UPDATE prompt_nodes SET active_version_id=?, updated_at=? WHERE id=?",
            (new_ver_id, now, node_id),
        )
        db.commit()

        return self.get_node(node_id, by_key=False)

    def compare_versions(self, version_id_1:
        str,
                         version_id_2: str) -> Dict[str, Any]:
        """对比两个版本的差异。"""
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)
        if not v1 or not v2:
            raise ValueError("版本不存在")

        return {
            "v1": v1.to_detail_dict(),
            "v2": v2.to_detail_dict(),
            "diff": {
                "system_changed": v1.system_prompt != v2.system_prompt,
                "user_changed": v1.user_template != v2.user_template,
            },
        }

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------

    def render(self, node_key:
        str,
               variables: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        """渲染指定节点的提示词。

        Args:
            node_key: 节点唯一标识
            variables: 模板变量字典

        Returns:
            {"system": ..., "user": ...} 或 None
        """
        node = self.get_node(node_key, by_key=True)
        if not node:
            return None

        var_map = variables or {}
        system = self._render_template(node.get_active_system(), var_map)
        user = self._render_template(node.get_active_user_template(), var_map)

        return {"system": system, "user": user}

    @staticmethod
    def _render_template(template: str, variables: Dict[str, Any]) -> str:
        """简单模板渲染：{variable} 替换。"""
        if not template:
            return ""

        class SafeDict(dict):
            """定义 `SafeDict`，作为基础设施层中的业务对象。

            职责: 承载本模块的状态、规则或协作入口。
            关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
            副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
            异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
            """
            def __missing__(self, key):
                """同步执行 `__missing__` 对应的业务步骤。

                职责: 位于基础设施层，负责上述行为，并把相关输入、输出和副作用集中在 `__missing__` 这一入口。
                关键输入:
                - key: 业务标识或配置键，用于定位目标记录。
                关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
                副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
                异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
                """
                return "{" + key + "}"

        try:
            return template.format_map(SafeDict(variables))
        except (KeyError, ValueError, IndexError):
            return template

    # ------------------------------------------------------------------
    # 统计 & 分组
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取提示词库统计。"""
        db = self._get_db()
        total_nodes = db.execute("SELECT COUNT(*) AS c FROM prompt_nodes").fetchone()["c"]
        total_templates = db.execute("SELECT COUNT(*) AS c FROM prompt_templates").fetchone()["c"]
        total_versions = db.execute("SELECT COUNT(*) AS c FROM prompt_versions").fetchone()["c"]
        builtin_count = db.execute(
            "SELECT COUNT(*) AS c FROM prompt_nodes WHERE is_builtin=1"
        ).fetchone()["c"]
        custom_count = total_nodes - builtin_count

        # 各分类数量
        cat_rows = db.execute(
            "SELECT category, COUNT(*) AS c FROM prompt_nodes GROUP BY category"
        ).fetchall()
        categories = {r["category"]: r["c"] for r in cat_rows}

        return {
            "total_nodes": total_nodes,
            "total_templates": total_templates,
            "total_versions": total_versions,
            "builtin_count": builtin_count,
            "custom_count": custom_count,
            "categories": categories,
        }

    def get_nodes_by_category(self) -> Dict[str, List[NodeInfo]]:
        """按分类分组的所有节点。"""
        nodes = self.list_nodes(include_versions=True)
        result: Dict[str, List[NodeInfo]] = {}
        for node in nodes:
            result.setdefault(node.category, []).append(node)
        return result

    def get_categories_info(self) -> List[Dict[str, Any]]:
        """返回分类定义列表（含节点计数）。"""
        stats = self.get_stats()
        cat_counts = stats.get("categories", {})
        result = []
        for cat_def in BUILTIN_CATEGORIES:
            info = dict(cat_def)
            info["count"] = cat_counts.get(cat_def["key"], 0)
            result.append(info)
        return result

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _attach_active_versions(self, nodes: List[NodeInfo]) -> None:
        """批量加载节点的激活版本。"""
        if not nodes:
            return
        db = self._get_db()
        ids = [n.active_version_id for n in nodes if n.active_version_id]
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        rows = db.execute(
            f"SELECT * FROM prompt_versions WHERE id IN ({placeholders})", ids
        ).fetchall()
        ver_map = {r["id"]: VersionInfo(dict(r)) for r in rows}
        for node in nodes:
            if node.active_version_id and node.active_version_id in ver_map:
                node.set_active_version(ver_map[node.active_version_id])

    @staticmethod
    def _get_current_version(db, node_id: str) -> Optional[VersionInfo]:
        """获取节点当前激活版本。"""
        row = db.execute("""
            SELECT v.* FROM prompt_versions v
            INNER JOIN prompt_nodes n ON n.active_version_id = v.id
            WHERE n.id = ?
        """, (node_id,)).fetchone()
        return VersionInfo(dict(row)) if row else None


# ------------------------------------------------------------------
# 单例
# ------------------------------------------------------------------

_manager_instance: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """获取全局 PromptManager 单例。"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PromptManager()
    return _manager_instance
