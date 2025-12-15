"""
生成路由 (Generation Router)
提供投标文件生成相关的 API 端点
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json

from core.logger import logger
from core.cache import cache  # 使用Redis缓存

router = APIRouter(prefix="/api/generation", tags=["generation"])

# 使用Redis缓存替代内存存储，任务状态TTL=24小时
TASK_STATUS_TTL = 86400


# ========== Pydantic Models ==========

class GenerateProposalRequest(BaseModel):
    """生成投标文件请求"""
    tenderFileId: str
    useTemporaryLogic: Optional[bool] = False
    taskId: Optional[str] = None


class RegenerateRequest(BaseModel):
    """重新生成请求"""
    feedback: str


# ========== API Endpoints ==========

@router.post("/generate")
async def generate_proposal(request: GenerateProposalRequest, background_tasks: BackgroundTasks):
    """
    生成投标文件
    
    Body:
        {
            "tenderFileId": "uuid",
            "useTemporaryLogic": false,
            "taskId": "optional-learning-task-id"
        }
    
    Returns:
        {"taskId": "uuid", "status": "processing"}
    """
    task_id = str(uuid.uuid4())
    
    # 初始化任务状态
    task_status = {
        "taskId": task_id,
        "status": "processing",
        "progress": 0,
        "message": "Generation task started",
        "createdAt": datetime.utcnow().isoformat(),
        "tenderFileId": request.tenderFileId,
        "useTemporaryLogic": request.useTemporaryLogic,
        "learningTaskId": request.taskId
    }
    
    # 存储到Redis，24小时过期
    cache.set(
        f"generation_task:{task_id}",
        task_status,
        ttl=TASK_STATUS_TTL
    )
    
    # 在后台执行生成任务
    background_tasks.add_task(process_generation_task, task_id, request)
    
    logger.info(f"Generation task started: {task_id} for tender file: {request.tenderFileId}")
    
    return {
        "taskId": task_id,
        "status": "processing",
        "message": "Generation task has been queued"
    }


@router.get("/status/{taskId}")
async def get_generation_status(taskId: str):
    """
    获取生成任务状态
    
    Args:
        taskId: 任务ID
    
    Returns:
        {
            "taskId": "uuid",
            "status": "processing|completed|failed",
            "progress": 0-100,
            "message": "...",
            "result": {...}
        }
    """
    task_json = cache.get(f"generation_task:{taskId}")
    
    if not task_json:
        raise HTTPException(status_code=404, detail=f"Generation task not found: {taskId}")
    
    task = task_json
    return task


@router.post("/validate/{taskId}")
async def validate_proposal(taskId: str):
    """
    验证生成的投标文件
    
    Args:
        taskId: 生成任务ID
    
    Returns:
        {
            "isValid": true,
            "violations": [],
            "score": 95.5,
            "recommendations": [...]
        }
    """
    task = generation_task_store.get(taskId)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Generation task not found: {taskId}")
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Task not completed yet. Current status: {task['status']}"
        )
    
    # TODO: 实现实际的验证逻辑
    # 1. 从任务结果中获取生成的文件
    # 2. 使用 MultiAgentEvaluator 进行评估
    # 3. 返回违规项和评分
    
    validation_result = {
        "isValid": True,
        "violations": [],
        "score": 92.5,
        "recommendations": [
            "Consider adding more technical details in section 3",
            "Ensure all required certifications are included"
        ],
        "evaluatedAt": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Validation completed for task: {taskId}, score: {validation_result['score']}")
    
    return validation_result


@router.post("/regenerate/{taskId}")
async def regenerate_proposal(taskId: str, request: RegenerateRequest, background_tasks: BackgroundTasks):
    """
    基于反馈重新生成投标文件
    
    Args:
        taskId: 原始生成任务ID
        request: {"feedback": "user feedback text"}
    
    Returns:
        {"taskId": "new-uuid", "status": "processing"}
    """
    # 从Redis获取原始任务
    original_task_json = cache.get(f"generation_task:{taskId}")
    
    if not original_task_json:
        raise HTTPException(status_code=404, detail=f"Original task not found: {taskId}")
    
    original_task = json.loads(original_task_json)
    
    # 创建新的生成任务
    new_task_id = str(uuid.uuid4())
    
    new_task_status = {
        "taskId": new_task_id,
        "status": "processing",
        "progress": 0,
        "message": "Regeneration task started with feedback",
        "createdAt": datetime.utcnow().isoformat(),
        "tenderFileId": original_task.get("tenderFileId"),
        "originalTaskId": taskId,
        "feedback": request.feedback,
        "isRegeneration": True
    }
    
    # 存储到Redis
    cache.set(
        f"generation_task:{new_task_id}",
        json.dumps(new_task_status),
        ttl=TASK_STATUS_TTL
    )
    
    # 在后台执行重新生成任务
    background_tasks.add_task(
        process_regeneration_task, 
        new_task_id, 
        original_task.get("tenderFileId"),
        request.feedback
    )
    
    logger.info(f"Regeneration task started: {new_task_id} based on task: {taskId}")
    
    return {
        "taskId": new_task_id,
        "status": "processing",
        "message": "Regeneration task has been queued"
    }


@router.get("/health")
async def generation_health():
    """生成服务健康检查"""
    return {
        "status": "healthy",
        "service": "generation",
        "activeTasks": len([t for t in generation_task_store.values() if t["status"] == "processing"])
    }


# ========== Background Task Handlers ==========

async def process_generation_task(task_id: str, request: GenerateProposalRequest):
    """
    后台处理生成任务
    
    使用Redis缓存存储任务状态
    """
    try:
        # 更新进度到Redis
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status["progress"] = 20
            task_status["message"] = "Loading tender document..."
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
        
        # TODO: 实际的生成逻辑
        # 1. 加载招标文件
        # 2. 提取需求
        # 3. 使用智能路由器决策
        # 4. 生成各章节内容
        # 5. 合并为完整文件
        
        # 模拟处理
        import asyncio
        await asyncio.sleep(1)
        
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status["progress"] = 50
            task_status["message"] = "Generating content..."
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
        
        await asyncio.sleep(2)
        
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status["progress"] = 80
            task_status["message"] = "Validating output..."
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
        
        await asyncio.sleep(1)
        
        # 更新为完成状态
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status.update({
                "status": "completed",
                "progress": 100,
                "message": "Generation completed successfully",
                "completedAt": datetime.utcnow().isoformat(),
                "result": {
                    "fileId": str(uuid.uuid4()),
                    "fileName": "generated_proposal.docx",
                    "chaptersGenerated": 8,
                    "totalWords": 15240,
                    "downloadUrl": f"/api/files/download/{uuid.uuid4()}"
                }
            })
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
        
        logger.info(f"Generation task completed: {task_id}")
    
    except Exception as e:
        logger.error(f"Generation task failed: {task_id}, error: {str(e)}")
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status.update({
                "status": "failed",
                "message": f"Generation failed: {str(e)}",
                "error": str(e)
            })
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)


async def process_regeneration_task(task_id: str, tender_file_id: str, feedback: str):
    """
    后台处理重新生成任务（基于反馈）
    """
    try:
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status["progress"] = 30
            task_status["message"] = f"Incorporating feedback: {feedback[:50]}..."
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
        
        # TODO: 实际的重新生成逻辑
        # 1. 解析用户反馈
        # 2. 调整生成策略
        # 3. 重新生成受影响的章节
        
        import asyncio
        await asyncio.sleep(3)
        
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status.update({
                "status": "completed",
                "progress": 100,
                "message": "Regeneration completed with feedback incorporated",
                "completedAt": datetime.utcnow().isoformat(),
                "result": {
                    "fileId": str(uuid.uuid4()),
                    "fileName": "regenerated_proposal.docx",
                    "chaptersRegenerated": 3,
                    "feedbackApplied": feedback
                }
            })
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
        
        logger.info(f"Regeneration task completed: {task_id}")
    
    except Exception as e:
        logger.error(f"Regeneration task failed: {task_id}, error: {str(e)}")
        task_json = cache.get(f"generation_task:{task_id}")
        if task_json:
            task_status = task_json
            task_status.update({
                "status": "failed",
                "message": f"Regeneration failed: {str(e)}",
                "error": str(e)
            })
            cache.set(f"generation_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
