"""
LLM 路由 - 大模型管理和对话
提供模型配置、管理和对话功能
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid
import json

from openai import AsyncOpenAI

from core.config import get_settings
from core.llm_router import LLMRouter
from core.logger import logger
from database.connection import db

router = APIRouter(prefix="/api/llm", tags=["LLM"])
settings = get_settings()
llm_router = LLMRouter()

# ========== Pydantic Models ==========

Provider = Literal["openai", "deepseek", "qwen", "ollama", "other"]


class ModelInfo(BaseModel):
    """模型信息（对齐前端字段）"""

    model_config = {"populate_by_name": True}

    id: str
    name: str
    provider: Provider
    endpoint: Optional[str] = None
    apiKey: Optional[str] = None
    modelName: Optional[str] = None
    temperature: float = 0.7
    maxTokens: int = 2000
    isActive: bool = True

    # 向后兼容字段（旧脚本/旧前端可能依赖）
    description: Optional[str] = None
    is_default: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


class ModelCreate(BaseModel):
    """创建模型请求（对齐前端字段）"""

    model_config = {"populate_by_name": True}

    name: str
    provider: Provider
    endpoint: Optional[str] = None
    apiKey: Optional[str] = None
    modelName: Optional[str] = None
    temperature: float = 0.7
    maxTokens: int = 2000
    isActive: bool = True

    # 兼容旧字段输入
    description: Optional[str] = None
    is_default: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


class ModelUpdate(BaseModel):
    """更新模型请求（对齐前端字段）"""

    model_config = {"populate_by_name": True}

    name: Optional[str] = None
    provider: Optional[Provider] = None
    endpoint: Optional[str] = None
    apiKey: Optional[str] = None
    modelName: Optional[str] = None
    temperature: Optional[float] = None
    maxTokens: Optional[int] = None
    isActive: Optional[bool] = None

    # 兼容旧字段输入
    description: Optional[str] = None
    is_default: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    modelId: Optional[str] = None
    conversationId: Optional[str] = None

class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    conversationId: str
    model: str
    timestamp: str

# ========== Helper Functions ==========

def mask_api_key(key: str) -> str:
    """隐藏API key，只显示前8位"""
    if len(key) <= 8:
        return key[:4] + "****"
    return key[:8] + "****" + key[-4:]


CUSTOM_MODELS_CONFIG_KEY = "custom_llm_models"


def _normalize_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return None
    return None


def _load_custom_models() -> List[Dict[str, Any]]:
    try:
        row = db.query_one(
            "SELECT config_value FROM system_config WHERE config_key=%s",
            (CUSTOM_MODELS_CONFIG_KEY,),
        )
        if not row:
            return []
        value = _normalize_json_value(row.get("config_value"))
        return value if isinstance(value, list) else []
    except Exception as e:
        logger.warning(f"Failed to load custom llm models from system_config: {e}")
        return []


def _save_custom_models(models: List[Dict[str, Any]]) -> None:
    payload = json.dumps(models, ensure_ascii=False)
    db.execute(
        """
        INSERT INTO system_config (config_key, config_value, description)
        VALUES (%s, (%s)::jsonb, %s)
        ON CONFLICT (config_key)
        DO UPDATE SET config_value=EXCLUDED.config_value, updated_at=now()
        """,
        (CUSTOM_MODELS_CONFIG_KEY, payload, "自定义LLM模型配置"),
    )


def _builtin_models() -> List[ModelInfo]:
    models: List[ModelInfo] = []

    deepseek_masked = (
        mask_api_key(settings.DEEPSEEK_API_KEY) if settings.DEEPSEEK_API_KEY else None
    )
    models.append(
        ModelInfo(
            id="deepseek-chat",
            name="DeepSeek Chat",
            provider="deepseek",
            endpoint=settings.DEEPSEEK_BASE_URL,
            apiKey=deepseek_masked,
            modelName=settings.DEEPSEEK_MODEL,
            isActive=True,
            description="DeepSeek 深度求索，擅长内容生成和理解",
            is_default=True,
            api_key=deepseek_masked,
            base_url=settings.DEEPSEEK_BASE_URL,
            model_name=settings.DEEPSEEK_MODEL,
        )
    )

    qwen_masked = mask_api_key(settings.QWEN_API_KEY) if settings.QWEN_API_KEY else None
    models.append(
        ModelInfo(
            id="qwen-plus",
            name="通义千问 Plus",
            provider="qwen",
            endpoint=settings.QWEN_BASE_URL,
            apiKey=qwen_masked,
            modelName=settings.QWEN_MODEL,
            isActive=True,
            description="阿里云千问模型，中文优化，适合分析评估",
            is_default=False,
            api_key=qwen_masked,
            base_url=settings.QWEN_BASE_URL,
            model_name=settings.QWEN_MODEL,
        )
    )

    # 内置 Ollama 模型（本地）
    models.append(
        ModelInfo(
            id="ollama-qwen3-8b",
            name="千问3 8B（Ollama）",
            provider="ollama",
            endpoint="http://host.docker.internal:11434/v1",
            apiKey=None,
            modelName="qwen3:8b",
            isActive=True,
            description="本地 Ollama 模型：qwen3:8b",
            is_default=False,
            api_key=None,
            base_url="http://host.docker.internal:11434/v1",
            model_name="qwen3:8b",
        )
    )

    return models


def _builtin_openai_compat_config(model_id: str) -> Optional[Dict[str, Any]]:
    """部分内置模型需要走 OpenAI 兼容接口（例如 Ollama）。"""
    if model_id == "ollama-qwen3-8b":
        return {
            "provider": "ollama",
            "endpoint": "http://host.docker.internal:11434/v1",
            "apiKey": "ollama",
            "modelName": "qwen3:8b",
            "temperature": 0.7,
            "maxTokens": 2000,
            "isActive": True,
        }
    return None


def _find_model(model_id: str) -> Optional[Dict[str, Any]]:
    for m in _load_custom_models():
        if m.get("id") == model_id:
            return m
    return None


def _to_model_info(model: Dict[str, Any]) -> ModelInfo:
    api_key = model.get("apiKey")
    masked = mask_api_key(api_key) if isinstance(api_key, str) and api_key else None
    return ModelInfo(
        id=model.get("id"),
        name=model.get("name"),
        provider=model.get("provider"),
        endpoint=model.get("endpoint"),
        apiKey=masked,
        modelName=model.get("modelName"),
        temperature=float(model.get("temperature", 0.7)),
        maxTokens=int(model.get("maxTokens", 2000)),
        isActive=bool(model.get("isActive", True)),

        # 兼容输出
        description=model.get("description") or "自定义模型",
        is_default=bool(model.get("is_default", False)),
        api_key=masked,
        base_url=model.get("endpoint"),
        model_name=model.get("modelName"),
    )


def _default_endpoint(provider: str) -> Optional[str]:
    if provider == "openai":
        return "https://api.openai.com/v1"
    if provider == "deepseek":
        return settings.DEEPSEEK_BASE_URL
    if provider == "qwen":
        return settings.QWEN_BASE_URL
    if provider == "ollama":
        return "http://host.docker.internal:11434/v1"
    return None


async def _chat_via_openai_compat(
    *,
    endpoint: str,
    api_key: str,
    model_name: str,
    message: str,
    temperature: float,
    max_tokens: int,
) -> str:
    client = AsyncOpenAI(api_key=api_key, base_url=endpoint)
    resp = await client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": message}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""

# ========== API Endpoints ==========

@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """
    获取所有可用的模型列表
    包括系统内置模型和用户自定义模型
    """
    models = _builtin_models()
    for m in _load_custom_models():
        try:
            models.append(_to_model_info(m))
        except Exception as e:
            logger.warning(f"Skip invalid custom model record: {e}")
    return models

@router.post("/models", response_model=ModelInfo)
async def add_model(request: ModelCreate):
    """
    添加自定义模型配置
    """
    model_id = f"custom-{uuid.uuid4().hex[:8]}"
    provider = request.provider
    endpoint = request.endpoint or request.base_url or _default_endpoint(provider)
    api_key = request.apiKey or request.api_key
    model_name = request.modelName or request.model_name or request.name

    if provider != "ollama" and not api_key:
        raise HTTPException(status_code=400, detail="API Key 不能为空")
    if provider == "ollama" and not api_key:
        api_key = "ollama"
    if provider in ("openai", "deepseek", "qwen", "ollama") and not endpoint:
        raise HTTPException(status_code=400, detail="API 端点不能为空")

    record: Dict[str, Any] = {
        "id": model_id,
        "name": request.name,
        "provider": provider,
        "endpoint": endpoint,
        "apiKey": api_key,
        "modelName": model_name,
        "temperature": request.temperature,
        "maxTokens": request.maxTokens,
        "isActive": request.isActive,
        "description": request.description,
        "is_default": bool(request.is_default),
        "createdAt": datetime.utcnow().isoformat(),
    }

    try:
        models = _load_custom_models()
        models.append(record)
        _save_custom_models(models)
        logger.info(f"Added custom model: {request.name} (provider: {provider})")
        return _to_model_info(record)
    except Exception as e:
        logger.error(f"Failed to add model: {e}")
        raise HTTPException(status_code=500, detail=f"添加模型失败: {str(e)}")

@router.put("/models/{model_id}", response_model=ModelInfo)
async def update_model(model_id: str, request: ModelUpdate):
    """
    更新模型配置
    """
    if model_id in ["deepseek-chat", "qwen-plus", "openai-gpt4"]:
        raise HTTPException(status_code=400, detail="不能编辑系统内置模型")

    try:
        models = _load_custom_models()
        found = False
        updated: Optional[Dict[str, Any]] = None
        for m in models:
            if m.get("id") != model_id:
                continue
            found = True
            if request.name is not None:
                m["name"] = request.name
            if request.provider is not None:
                m["provider"] = request.provider
            if request.endpoint is not None:
                m["endpoint"] = request.endpoint
            if request.base_url is not None:
                m["endpoint"] = request.base_url
            if request.apiKey is not None or request.api_key is not None:
                # 允许前端不传/传空以保持原值
                candidate = request.apiKey or request.api_key
                if candidate and "****" not in candidate:
                    m["apiKey"] = candidate
            if request.modelName is not None:
                m["modelName"] = request.modelName
            if request.model_name is not None:
                m["modelName"] = request.model_name
            if request.temperature is not None:
                m["temperature"] = request.temperature
            if request.maxTokens is not None:
                m["maxTokens"] = request.maxTokens
            if request.isActive is not None:
                m["isActive"] = request.isActive
            if request.description is not None:
                m["description"] = request.description
            if request.is_default is not None:
                m["is_default"] = bool(request.is_default)
            m["updatedAt"] = datetime.utcnow().isoformat()
            updated = m
            break

        if not found or not updated:
            raise HTTPException(status_code=404, detail="模型不存在")

        _save_custom_models(models)
        return _to_model_info(updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """
    删除自定义模型
    """
    # 不允许删除系统内置模型
    if model_id in ["deepseek-chat", "qwen-plus", "openai-gpt4"]:
        raise HTTPException(status_code=400, detail="不能删除系统内置模型")

    try:
        models = _load_custom_models()
        new_models = [m for m in models if m.get("id") != model_id]
        if len(new_models) == len(models):
            raise HTTPException(status_code=404, detail="模型不存在")
        _save_custom_models(new_models)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/models/{model_id}/test")
async def test_model(model_id: str):
    """
    测试模型连接
    """
    # 使用简单的测试提示
    test_message = "你好，请回复“连接成功”"

    # 内置 OpenAI-compat（Ollama 等）
    builtin_compat = _builtin_openai_compat_config(model_id)
    if builtin_compat:
        if not builtin_compat.get("isActive", True):
            raise HTTPException(status_code=400, detail="模型未激活")
        try:
            response = await _chat_via_openai_compat(
                endpoint=builtin_compat.get("endpoint"),
                api_key=builtin_compat.get("apiKey") or "ollama",
                model_name=builtin_compat.get("modelName"),
                message=test_message,
                temperature=float(builtin_compat.get("temperature", 0.7)),
                max_tokens=int(builtin_compat.get("maxTokens", 2000)),
            )
            return {
                "success": True,
                "message": "模型连接测试成功",
                "provider": builtin_compat.get("provider"),
                "response": response[:100] + "..." if len(response) > 100 else response,
            }
        except Exception as e:
            logger.error(f"Model test failed for builtin compat model {model_id}: {e}")
            raise HTTPException(status_code=500, detail=f"模型连接测试失败: {str(e)}")

    # 自定义模型
    custom = _find_model(model_id)
    if custom:
        if not custom.get("isActive", True):
            raise HTTPException(status_code=400, detail="模型未激活")
        provider = custom.get("provider")
        endpoint = custom.get("endpoint")
        api_key = custom.get("apiKey") or "ollama"
        model_name = custom.get("modelName") or custom.get("name")
        try:
            response = await _chat_via_openai_compat(
                endpoint=endpoint,
                api_key=api_key,
                model_name=model_name,
                message=test_message,
                temperature=float(custom.get("temperature", 0.7)),
                max_tokens=int(custom.get("maxTokens", 2000)),
            )
            return {
                "success": True,
                "message": "模型连接测试成功",
                "provider": provider,
                "response": response[:100] + "..." if len(response) > 100 else response,
            }
        except Exception as e:
            logger.error(f"Model test failed for custom model {model_id}: {e}")
            raise HTTPException(status_code=500, detail=f"模型连接测试失败: {str(e)}")

    # 系统内置模型
    try:
        from core.llm_router import TaskType
        prefer_model = "deepseek" if "deepseek" in model_id else "qwen"
        response = await llm_router.generate_text(
            prompt=test_message,
            task_type=TaskType.GENERATION,
            model_name=prefer_model,
        )
        return {
            "success": True,
            "message": "模型连接测试成功",
            "response": response[:100] + "..." if len(response) > 100 else response,
        }
    except Exception as e:
        logger.error(f"Model test failed for builtin model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"模型连接测试失败: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与LLM进行对话
    """
    # 确定使用的模型
    model_id = request.modelId or "deepseek-chat"
    conversation_id = request.conversationId or str(uuid.uuid4())

    # 内置 OpenAI-compat（Ollama 等）
    builtin_compat = _builtin_openai_compat_config(model_id)
    if builtin_compat:
        if not builtin_compat.get("isActive", True):
            raise HTTPException(status_code=400, detail="模型未激活")
        try:
            response = await _chat_via_openai_compat(
                endpoint=builtin_compat.get("endpoint"),
                api_key=builtin_compat.get("apiKey") or "ollama",
                model_name=builtin_compat.get("modelName"),
                message=request.message,
                temperature=float(builtin_compat.get("temperature", 0.7)),
                max_tokens=int(builtin_compat.get("maxTokens", 2000)),
            )
            logger.info(f"Chat completed for conversation {conversation_id} using builtin compat {model_id}")
            return ChatResponse(
                content=response,
                conversationId=conversation_id,
                model=model_id,
                timestamp=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            logger.error(f"Chat failed for builtin compat model {model_id}: {e}")
            raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

    # 自定义模型
    custom = _find_model(model_id)
    if custom:
        if not custom.get("isActive", True):
            raise HTTPException(status_code=400, detail="模型未激活")
        try:
            response = await _chat_via_openai_compat(
                endpoint=custom.get("endpoint"),
                api_key=custom.get("apiKey") or "ollama",
                model_name=custom.get("modelName") or custom.get("name"),
                message=request.message,
                temperature=float(custom.get("temperature", 0.7)),
                max_tokens=int(custom.get("maxTokens", 2000)),
            )
            logger.info(f"Chat completed for conversation {conversation_id} using custom {model_id}")
            return ChatResponse(
                content=response,
                conversationId=conversation_id,
                model=model_id,
                timestamp=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            logger.error(f"Chat failed for custom model {model_id}: {e}")
            raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

    # 系统内置模型
    try:
        prefer_model = "deepseek" if "deepseek" in model_id else "qwen"
        from core.llm_router import TaskType
        response = await llm_router.generate_text(
            prompt=request.message,
            task_type=TaskType.GENERATION,
            model_name=prefer_model,
        )
        logger.info(f"Chat completed for conversation {conversation_id} using {prefer_model}")
        return ChatResponse(
            content=response,
            conversationId=conversation_id,
            model=model_id,
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")
