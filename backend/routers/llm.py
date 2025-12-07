"""
LLM 路由 - 大模型管理和对话
提供模型配置、管理和对话功能
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from core.config import get_settings
from core.llm_router import LLMRouter
from core.logger import logger
from database.connection import db

router = APIRouter(prefix="/api/llm", tags=["LLM"])
settings = get_settings()
llm_router = LLMRouter()

# ========== Pydantic Models ==========

class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    provider: str
    description: str
    is_default: bool = False
    api_key: Optional[str] = None  # 不返回完整key，只返回前几位
    base_url: Optional[str] = None
    model_name: Optional[str] = None

class ModelCreate(BaseModel):
    """创建模型请求"""
    name: str
    provider: str  # deepseek, qwen, openai, etc.
    description: str
    api_key: str
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    is_default: bool = False

class ModelUpdate(BaseModel):
    """更新模型请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    is_default: Optional[bool] = None

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

# ========== API Endpoints ==========

@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """
    获取所有可用的模型列表
    包括系统内置模型和用户自定义模型
    """
    # 系统内置模型
    builtin_models = [
        ModelInfo(
            id="deepseek-chat",
            name="DeepSeek Chat",
            provider="deepseek",
            description="DeepSeek 深度求索，擅长内容生成和理解",
            is_default=True,
            api_key=mask_api_key(settings.DEEPSEEK_API_KEY) if settings.DEEPSEEK_API_KEY else None,
            base_url=settings.DEEPSEEK_BASE_URL,
            model_name=settings.DEEPSEEK_MODEL
        ),
        ModelInfo(
            id="qwen-plus",
            name="通义千问 Plus",
            provider="qwen",
            description="阿里云千问模型，中文优化，适合分析评估",
            api_key=mask_api_key(settings.QWEN_API_KEY) if settings.QWEN_API_KEY else None,
            base_url=settings.QWEN_BASE_URL,
            model_name=settings.QWEN_MODEL
        ),
    ]
    
    # TODO: 从数据库获取用户自定义模型
    # try:
    #     custom_models = db.query("SELECT * FROM custom_models WHERE deleted_at IS NULL")
    #     for model in custom_models:
    #         builtin_models.append(ModelInfo(**model))
    # except Exception as e:
    #     logger.warning(f"Failed to load custom models: {e}")
    
    return builtin_models

@router.post("/models", response_model=ModelInfo)
async def add_model(request: ModelCreate):
    """
    添加自定义模型配置
    """
    model_id = f"custom-{uuid.uuid4().hex[:8]}"
    
    try:
        # TODO: 保存到数据库
        # db.execute(
        #     """INSERT INTO custom_models (id, name, provider, description, api_key, base_url, model_name, is_default)
        #        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        #     (model_id, request.name, request.provider, request.description, 
        #      request.api_key, request.base_url, request.model_name, request.is_default)
        # )
        
        logger.info(f"Added custom model: {request.name} (provider: {request.provider})")
        
        return ModelInfo(
            id=model_id,
            name=request.name,
            provider=request.provider,
            description=request.description,
            is_default=request.is_default,
            api_key=mask_api_key(request.api_key),
            base_url=request.base_url,
            model_name=request.model_name
        )
    except Exception as e:
        logger.error(f"Failed to add model: {e}")
        raise HTTPException(status_code=500, detail=f"添加模型失败: {str(e)}")

@router.put("/models/{model_id}", response_model=ModelInfo)
async def update_model(model_id: str, request: ModelUpdate):
    """
    更新模型配置
    """
    # TODO: 实现数据库更新逻辑
    raise HTTPException(status_code=501, detail="暂未实现")

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """
    删除自定义模型
    """
    # 不允许删除系统内置模型
    if model_id in ["deepseek-chat", "qwen-plus", "openai-gpt4"]:
        raise HTTPException(status_code=400, detail="不能删除系统内置模型")
    
    # TODO: 实现数据库删除逻辑（软删除）
    raise HTTPException(status_code=501, detail="暂未实现")

@router.post("/models/{model_id}/test")
async def test_model(model_id: str):
    """
    测试模型连接
    """
    try:
        # 使用简单的测试提示
        test_message = "你好，请回复'连接成功'"
        
        # 根据model_id选择对应的模型进行测试
        from core.llm_router import TaskType
        prefer_model = "deepseek" if "deepseek" in model_id else "qwen"
        
        response = await llm_router.generate_text(
            prompt=test_message,
            task_type=TaskType.GENERATION,
            model_name=prefer_model
        )
        
        return {
            "success": True,
            "message": "模型连接测试成功",
            "response": response[:100] + "..." if len(response) > 100 else response
        }
    except Exception as e:
        logger.error(f"Model test failed for {model_id}: {e}")
        return {
            "success": False,
            "message": f"模型连接测试失败: {str(e)}"
        }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与LLM进行对话
    """
    try:
        # 确定使用的模型
        model_id = request.modelId or "deepseek-chat"
        prefer_model = "deepseek" if "deepseek" in model_id else "qwen"
        
        # 生成或使用现有的对话ID
        conversation_id = request.conversationId or str(uuid.uuid4())
        
        # 调用LLM - 使用正确的方法名
        from core.llm_router import TaskType
        response = await llm_router.generate_text(
            prompt=request.message,
            task_type=TaskType.GENERATION,
            model_name=prefer_model
        )
        
        # TODO: 保存对话历史到数据库
        
        logger.info(f"Chat completed for conversation {conversation_id} using {prefer_model}")
        
        return ChatResponse(
            content=response,
            conversationId=conversation_id,
            model=model_id,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")
