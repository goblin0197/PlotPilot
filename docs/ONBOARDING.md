# PlotPilot Onboarding Guide

## Project Overview

PlotPilot 是一个 AI 驱动的长篇创作平台，核心能力包括自动驾驶生成、知识图谱管理、风格分析和前端创作工作台。

主要技术栈：

- Backend: Python, FastAPI, Pydantic
- Frontend: Vue 3, TypeScript, Vite, Naive UI, Pinia
- Desktop: Tauri
- Retrieval: FAISS / ChromaDB 相关向量能力
- Testing: pytest

本指南基于 `.understand-anything/knowledge-graph.json` 生成。本次图谱分析了 614 个文件，并按项目约定排除了 `tests/` 与 `tools/python_embed/`。

## Architecture Layers

### 入口与根模块层

项目启动入口和根级模块。

关键文件：

- `__main__.py`
- `cli.py`
- `load_env.py`

### 项目配置层

项目根配置、依赖清单和工具配置。

关键文件：

- `.env.example`
- `pyproject.toml`
- `pytest.ini`
- `frontend/package.json`

### 文档层

项目说明、设计记录和操作文档。

关键文件：

- `README.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `README_LOGGING.md`

### CI/CD 层

持续集成和自动化工作流配置。

关键文件：

- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`

### 应用层

`application/` 负责用例编排、应用服务和 DTO 转换。这里应调用领域层能力并协调基础设施实现，不应把核心业务规则散落到接口层或基础设施层。

建议优先阅读：

- `application/ai/llm_control_service.py`
- `application/engine/services/autopilot_daemon.py`
- `application/engine/services/memory_engine.py`
- `application/workflows/auto_novel_generation_workflow.py`
- `application/world/services/knowledge_graph_service.py`

### 领域层

`domain/` 承载核心业务实体、值对象、领域服务和仓储接口。该层应保持纯粹，避免依赖 FastAPI、数据库实现、LLM SDK 或前端概念。

建议优先阅读：

- `domain/ai/services/llm_service.py`
- `domain/ai/services/vector_store.py`
- `domain/ai/services/embedding_service.py`
- `domain/knowledge/`
- `domain/novel/`

### 前端体验层

`frontend/` 包含 Vue、TypeScript、Vite、Naive UI、Pinia 和 Tauri 相关用户界面代码。

建议优先阅读：

- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/api/`
- `frontend/src/components/workbench/`
- `frontend/src/components/autopilot/`
- `frontend/src/components/knowledge/`

### 基础设施层

`infrastructure/` 实现数据库、向量检索、LLM 客户端、持久化仓储和外部服务适配。

建议优先阅读：

- `infrastructure/ai/llm_client.py`
- `infrastructure/ai/local_embedding_service.py`
- `infrastructure/ai/chromadb_vector_store.py`
- `infrastructure/persistence/`
- `infrastructure/persistence/database/migrations/`

### 接口层

`interfaces/` 负责 FastAPI 路由、依赖注入、请求响应模型和外部入口。接口层应保持薄，避免承载复杂业务决策。

建议优先阅读：

- `interfaces/api/dependencies.py`
- `interfaces/api/middleware/`
- `interfaces/api/v1/`
- `interfaces/api/stats/routers/stats.py`

### 工具与构建层

`scripts/` 和 `tools/aitext.bat` 用于本地开发、健康检查、评估、启动和打包辅助。

建议优先阅读：

- `scripts/check_health.py`
- `scripts/dev-local.sh`
- `scripts/evaluation/`
- `tools/aitext.bat`

## Key Concepts

- 后端遵循 DDD 分层：`domain -> application -> infrastructure -> interfaces`。
- `domain/` 定义核心业务概念和抽象接口，不应依赖外部技术实现。
- `application/` 编排具体用例，是业务流程和领域对象之间的协调层。
- `infrastructure/` 承担数据库、向量检索、LLM 客户端和外部服务实现。
- `interfaces/` 负责 HTTP/API/CLI 入口和请求响应边界。
- 前端围绕工作台、自动驾驶、知识图谱、世界观和章节编辑组织用户流程。
- 守护进程、章节生成、知识落库和向量索引更新是项目中最重要的业务链路之一。

## Guided Tour

1. 项目总览：阅读 `README.md`、`pyproject.toml` 和 `frontend/package.json`，理解项目定位、技术栈和运行边界。
2. 后端入口：查看 `__main__.py`、`cli.py` 和 `interfaces/api/`，理解请求如何进入应用服务。
3. DDD 核心：沿 `domain/` 到 `application/` 阅读，确认领域模型、用例编排和依赖边界。
4. 基础设施实现：阅读 `infrastructure/ai/` 与 `infrastructure/persistence/`，理解 LLM、检索和数据库能力如何接入。
5. 前端体验：从 `frontend/src/main.ts` 和 `frontend/src/App.vue` 进入，再看 `frontend/src/components/workbench/`。
6. 验证与工具：阅读 `scripts/check_health.py`、`scripts/dev-local.sh` 和 `tools/aitext.bat`，理解本地运行和维护方式。

## File Map

### Backend Entry

- `__main__.py`: Python 模块入口。
- `cli.py`: 命令行入口。
- `load_env.py`: 环境变量加载辅助。

### Domain

- `domain/ai/services/`: LLM、向量、摘要等领域服务抽象。
- `domain/knowledge/`: 知识图谱、三元组和检索相关领域概念。
- `domain/novel/`: 小说、章节和创作流程相关领域概念。

### Application

- `application/ai/`: LLM 控制、输出清洗、JSON 提取和知识 LLM 契约。
- `application/engine/`: 自动驾驶、上下文预算、记忆引擎和主题能力。
- `application/world/`: 世界观、角色、地点和 Bible 生成服务。
- `application/workflows/`: 跨服务的自动生成工作流。

### Infrastructure

- `infrastructure/ai/`: LLM 客户端、本地 embedding、ChromaDB/向量存储。
- `infrastructure/persistence/`: 仓储实现、数据库映射、迁移和存储细节。

### Interfaces

- `interfaces/api/dependencies.py`: FastAPI 依赖注入集中点，新人改接口前应先读这里。
- `interfaces/api/v1/`: API v1 路由模块。
- `interfaces/api/middleware/`: 错误处理、日志等接口层中间件。

### Frontend

- `frontend/src/api/`: 前端 API 客户端。
- `frontend/src/components/workbench/`: 创作工作台核心界面。
- `frontend/src/components/autopilot/`: 自动驾驶状态、日志、章节流和指标界面。
- `frontend/src/components/knowledge/`: 知识图谱和三元组管理界面。
- `frontend/src/stores/`: 前端状态管理。

### Tooling

- `scripts/check_health.py`: 健康检查。
- `scripts/dev-local.sh`: 本地开发启动辅助。
- `scripts/evaluation/`: 评估脚本。
- `tools/aitext.bat`: Windows 启动器，处理嵌入式 Python、pip 和 GUI 启动流程。

## Complexity Hotspots

这些文件或区域复杂度较高，新人修改前建议先读相关调用链和测试/文档：

- `application/ai/llm_control_service.py`
- `application/audit/services/chapter_review_service.py`
- `application/blueprint/services/continuous_planning_service.py`
- `application/engine/services/autopilot_daemon.py`
- `application/engine/services/context_budget_allocator.py`
- `application/engine/services/memory_engine.py`
- `application/engine/theme/theme_agent.py`
- `application/workflows/auto_novel_generation_workflow.py`
- `application/world/services/auto_bible_generator.py`
- `application/world/services/chapter_narrative_sync.py`
- `application/world/services/knowledge_graph_service.py`
- `interfaces/api/dependencies.py`
- `infrastructure/ai/prompts/prompts_defaults.json`
- `frontend/src/components/workbench/`
- `frontend/src/components/autopilot/`

## Practical Advice For New Contributors

- 先确认改动属于哪一层，再动代码。
- 后端新增业务能力时，优先从 `domain/` 和 `application/` 建模，再接入 `infrastructure/` 和 `interfaces/`。
- 不要让 FastAPI 路由直接承载复杂业务流程。
- 不要让基础设施实现反向污染领域层。
- 前端改工作台时，先找 `frontend/src/api/`、相关 `components/workbench/` 组件和状态管理入口。
- 修改自动驾驶、章节生成、知识图谱或向量检索时，额外检查落库、索引更新和上下文组装链路。

## Related Artifacts

- Knowledge graph: `.understand-anything/knowledge-graph.json`
- Dashboard: use the tokenized local URL printed when `/understand` launches the dashboard
- Ignore rules: `.understand-anything/.understandignore`
