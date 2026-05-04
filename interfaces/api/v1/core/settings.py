"""LLM 配置管理 API（兼容旧路由，底层委托给 LLMControlService）。"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from application.ai.llm_control_service import LLMControlService, LLMProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings/llm-configs", tags=["settings"])

_service = LLMControlService()


# ── schemas (兼容旧接口) ──────────────────────────────

class ConfigCreate(BaseModel):
    """定义 `ConfigCreate`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    name: str
    provider: str  # "openai" | "anthropic"
    api_key: str
    base_url: str = ""
    model: str = ""
    system_model: str = ""
    writing_model: str = ""


class ConfigUpdate(BaseModel):
    """定义 `ConfigUpdate`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    system_model: Optional[str] = None
    writing_model: Optional[str] = None


class FetchModelsRequest(BaseModel):
    """定义 `FetchModelsRequest`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    provider: str
    api_key: str
    base_url: str


def _profile_to_dict(p: LLMProfile) -> dict:
    """将 LLMProfile 转换为旧接口的 dict 格式。"""
    return {
        "id": p.id,
        "name": p.name,
        "provider": p.protocol,
        "api_key": p.api_key,
        "base_url": p.base_url,
        "model": p.model,
        "system_model": p.model,
        "writing_model": p.model,
    }


# ── endpoints ──────────────────────────────────────────

@router.get("/")
def list_configs():
    """同步读取 `configs` 相关的数据或状态。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `list_configs` 这一入口。
    关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
    关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    config = _service.get_config()
    return [_profile_to_dict(p) for p in config.profiles]


@router.post("/")
def create_config(body: ConfigCreate):
    """同步组装 `config` 所需的结构化结果。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `create_config` 这一入口。
    关键输入:
    - body: 结构化数据载荷，通常来自请求、数据库行或上游服务。
    关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    config = _service.get_config()
    new_profile = LLMProfile(
        id=f"profile-{len(config.profiles) + 1}",
        name=body.name,
        preset_key="custom-openai-compatible",
        protocol=body.provider,  # type: ignore[arg-type]
        base_url=body.base_url,
        api_key=body.api_key,
        model=body.model or body.system_model or body.writing_model,
    )
    config.profiles.append(new_profile)
    saved = _service.save_config(config)
    return _profile_to_dict(saved.profiles[-1])


@router.put("/{config_id}")
def update_config(config_id: str, body: ConfigUpdate):
    """同步写入、更新或清理 `config` 相关状态。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `update_config` 这一入口。
    关键输入:
    - config_id: 业务标识或配置键，用于定位目标记录。
    - body: 结构化数据载荷，通常来自请求、数据库行或上游服务。
    关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 会显式抛出 `HTTPException`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
    """
    config = _service.get_config()
    for i, p in enumerate(config.profiles):
        if p.id == config_id:
            update_data = body.model_dump(exclude_none=True)
            # 映射旧字段名到新字段名
            if "provider" in update_data:
                update_data["protocol"] = update_data.pop("provider")
            updated = p.model_copy(update={k: v for k, v in update_data.items() if hasattr(p, k)})
            config.profiles[i] = updated
            _service.save_config(config)
            return _profile_to_dict(updated)
    raise HTTPException(404, "Config not found")


@router.delete("/{config_id}")
def delete_config(config_id: str):
    """同步写入、更新或清理 `config` 相关状态。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `delete_config` 这一入口。
    关键输入:
    - config_id: 业务标识或配置键，用于定位目标记录。
    关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 会显式抛出 `HTTPException`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
    """
    config = _service.get_config()
    original_len = len(config.profiles)
    config.profiles = [p for p in config.profiles if p.id != config_id]
    if len(config.profiles) == original_len:
        raise HTTPException(404, "Config not found")
    _service.save_config(config)
    return {"ok": True}


@router.post("/{config_id}/activate")
def activate_config(config_id: str):
    """同步执行 `activate_config` 对应的业务步骤。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `activate_config` 这一入口。
    关键输入:
    - config_id: 业务标识或配置键，用于定位目标记录。
    关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 会显式抛出 `HTTPException`；底层依赖的数据库、文件、网络或校验异常会按调用栈透传。
    """
    config = _service.get_config()
    ids = {p.id for p in config.profiles}
    if config_id not in ids:
        raise HTTPException(404, "Config not found")
    config.active_profile_id = config_id
    _service.save_config(config)
    return {"ok": True}


@router.post("/fetch-models")
async def fetch_models(body: FetchModelsRequest):
    """复用 llm-control/models 端点的逻辑。"""
    from interfaces.api.v1.workbench.llm_control import list_models
    from interfaces.api.v1.workbench.llm_control import ModelListRequest

    payload = ModelListRequest(
        protocol=body.provider,
        base_url=body.base_url,
        api_key=body.api_key,
    )
    result = await list_models(payload)
    return [m.id for m in result.items]


# ── embedding endpoints（数据库持久化）──────────────────

embedding_router = APIRouter(prefix="/settings/embedding", tags=["settings"])


class EmbeddingConfigUpdate(BaseModel):
    """定义 `EmbeddingConfigUpdate`，作为接口层中的Pydantic 数据模型。

    职责: 承载 API、应用服务或配置层之间传递的结构化字段，并由 Pydantic 执行类型校验。
    关键输入输出: 字段、构造参数和公开方法共同定义可用数据形状；实例通常作为上游请求、应用服务或持久化流程的输入/输出。
    副作用: 类定义本身无外部副作用；实例化时可能执行字段默认值生成、类型转换或校验逻辑。
    异常/边界: 缺失必填字段、类型不匹配或违反校验规则时，由 Python、Pydantic 或调用方约定抛出异常。
    """
    model_config = {"protected_namespaces": ()}
    mode: str = "local"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    use_gpu: bool = True
    model_path: str = ""


@embedding_router.get("/")
def get_embedding_config():
    """获取当前嵌入模型配置（从数据库读取）。"""
    from application.ai.embedding_config_service import get_embedding_config_service
    svc = get_embedding_config_service()
    return svc.to_api_dict()


@embedding_router.put("/")
def update_embedding_config(body: EmbeddingConfigUpdate):
    """更新嵌入模型配置（持久化到数据库）。"""
    from application.ai.embedding_config_service import get_embedding_config_service
    svc = get_embedding_config_service()
    updated = svc.update_config(
        mode=body.mode,
        api_key=body.api_key,
        base_url=body.base_url,
        model=body.model,
        use_gpu=body.use_gpu,
        model_path=body.model_path,
    )
    return updated.to_api_dict()


@embedding_router.post("/fetch-models")
async def fetch_embedding_models(body: FetchModelsRequest):
    """异步读取 `embedding_models` 相关的数据或状态。

    职责: 位于接口层，负责上述行为，并把相关输入、输出和副作用集中在 `fetch_embedding_models` 这一入口。
    关键输入:
    - body: 结构化数据载荷，通常来自请求、数据库行或上游服务。
    关键输出: 返回由函数主体计算、查询或组装出的结果；具体结构由调用场景约定。
    副作用: 会在事件循环中等待异步 I/O 或后台任务。
    异常/边界: 不吞掉底层失败；数据库、文件、网络、LLM 或异步任务异常会按调用栈透传。
    """
    if not body.base_url:
        return []
    from interfaces.api.v1.workbench.llm_control import list_models
    from interfaces.api.v1.workbench.llm_control import ModelListRequest

    payload = ModelListRequest(
        protocol=body.provider,
        base_url=body.base_url,
        api_key=body.api_key,
    )
    result = await list_models(payload)
    return [m.id for m in result.items]
