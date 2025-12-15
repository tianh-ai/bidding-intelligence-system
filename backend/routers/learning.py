"""
逻辑学习路由 - 通过 MCP 客户端调用逻辑学习服务

按项目要求：逻辑学习必须通过 MCP 架构实现
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from core.mcp_client import get_logic_learning_client
from core.logger import logger

router = APIRouter()


# ========== 请求模型 ==========

class LearningStartRequest(BaseModel):
    """学习任务启动请求"""
    fileIds: List[str]
    learningType: str  # 'chapter' or 'global'
    chapterIds: Optional[List[str]] = None


class ChapterPairRequest(BaseModel):
    """章节对学习请求"""
    tender_chapter_id: str
    proposal_chapter_id: str
    boq_data: Optional[Dict[str, Any]] = None
    custom_rules: Optional[List[Dict[str, Any]]] = None


class FilePairRequest(BaseModel):
    """文件对学习请求"""
    tender_file_id: str
    proposal_file_id: str


# ========== API 端点 ==========

@router.post("/start")
async def start_learning_task(request: LearningStartRequest):
    """
    启动学习任务（章节级或全局级）
    
    POST /api/learning/start
    Body: {
        "fileIds": ["file1", "file2"],
        "learningType": "chapter",  // or "global"
        "chapterIds": ["ch1", "ch2"]  // optional, required for chapter learning
    }
    
    Returns:
        {"task_id": "uuid", "status": "processing"}
    """
    try:
        client = get_logic_learning_client()
        result = await client.start_learning(
            file_ids=request.fileIds,
            learning_type=request.learningType,
            chapter_ids=request.chapterIds
        )
        logger.info(f"MCP result: {result}")
        return {
            "taskId": result.get("task_id", ""),
            "status": result.get("status", "unknown"),
            "message": result.get("message", "Learning task started"),
            "source": "mcp"
        }
    except Exception as e:
        logger.error(f"MCP start learning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{taskId}")
async def get_learning_status(taskId: str):
    """
    获取学习任务状态
    
    GET /api/learning/status/{taskId}
    
    Returns:
        {taskId, status, progress, message, result}
    """
    try:
        client = get_logic_learning_client()
        status = await client.get_learning_status(task_id=taskId)
        
        logger.info(f"MCP status result: {status}")
        
        # 转换格式以保持前端兼容性
        return {
            "taskId": status.get("task_id", taskId),
            "status": status.get("status", "unknown"),
            "progress": status.get("progress", 0),
            "message": status.get("message", ""),
            "result": status.get("result"),
            "createdAt": status.get("created_at"),
            "completedAt": status.get("completed_at"),
            "source": "mcp"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"MCP get learning status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logic-db")
async def get_logic_database(category: Optional[str] = None):
    """
    获取逻辑库（所有已学习的逻辑规则）
    
    GET /api/learning/logic-db?category=general
    
    Returns:
        {
            "total_rules": int,
            "category_stats": [...],
            "recent_rules": [...]
        }
    """
    try:
        client = get_logic_learning_client()
        result = await client.get_logic_database(category=category)
        return {
            **result,
            "source": "mcp"
        }
    except Exception as e:
        logger.error(f"MCP get logic database failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
        # 获取全局级规则
        global_rules = db.query(
            """
            SELECT 'structure' as rule_type, id, tender_file_id, rule_content,
                   COALESCE(priority, 1.0)::float as confidence, created_at
            FROM global_structure_rules WHERE is_active = TRUE
            UNION ALL
            SELECT 'content' as rule_type, id, tender_file_id, rule_content,
                   COALESCE(priority, 1.0)::float as confidence, created_at
            FROM global_content_rules WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
        
        return {
            "chapterRules": chapter_rules or [],
            "globalRules": global_rules or [],
            "totalRules": len(chapter_rules or []) + len(global_rules or [])
        }

# 保留章节级和全局级学习的传统API（如果需要直接调用）
# 这些端点暂时保留，但建议迁移到 MCP 架构

class ChapterPairRequest(BaseModel):
    """章节对学习请求"""
    tender_chapter_id: str
    proposal_chapter_id: str
    boq_data: Optional[Dict[str, Any]] = None
    custom_rules: Optional[List[Dict[str, Any]]] = None


class FilePairRequest(BaseModel):
    """文件对学习请求"""
    tender_file_id: str
    proposal_file_id: str


# 注意：以下端点已被弃用，建议使用 /start 端点通过 MCP 调用
# 保留仅为向后兼容
