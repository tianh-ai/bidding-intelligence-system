"""
逻辑学习路由
提供章节级和全局级学习功能
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from engines import ChapterLogicEngine, GlobalLogicEngine
from database import db
from core.logger import logger
from core.cache import cache  # 使用Redis缓存
import uuid
from datetime import datetime
import json

router = APIRouter()
chapter_engine = ChapterLogicEngine()
global_engine = GlobalLogicEngine()

# 使用Redis缓存替代内存存储，任务状态TTL=24小时
TASK_STATUS_TTL = 86400


# ========== 请求模型 ==========

class LearningStartRequest(BaseModel):
    """学习任务启动请求"""
    fileIds: Optional[List[str]] = None
    folderPath: Optional[str] = None


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


# ========== 学习任务管理 ==========

@router.post("/start")
async def start_learning_task(request: LearningStartRequest, background_tasks: BackgroundTasks):
    """
    启动学习任务（章节级或全局级）
    
    Body:
        {
            "fileIds": ["file1", "file2"],  // 可选: 文件ID列表
            "folderPath": "/path/to/folder"  // 可选: 文件夹路径
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
        "message": "Learning task started",
        "createdAt": datetime.utcnow().isoformat(),
        "fileIds": request.fileIds or [],
        "folderPath": request.folderPath
    }
    
    # 存储到Redis，24小时过期
    await cache.set(
        f"learning_task:{task_id}",
        json.dumps(task_status),
        ttl=TASK_STATUS_TTL
    )
    
    # 在后台执行学习任务
    background_tasks.add_task(process_learning_task, task_id, request)
    
    logger.info(f"Learning task started: {task_id}")
    
    return {
        "taskId": task_id,
        "status": "processing",
        "message": "Learning task has been queued"
    }


@router.get("/status/{taskId}")
async def get_learning_status(taskId: str):
    """
    获取学习任务状态
    
    Args:
        taskId: 任务ID
    
    Returns:
        {taskId, status, progress, message, result}
    """
    task_json = await cache.get(f"learning_task:{taskId}")
    
    if not task_json:
        raise HTTPException(status_code=404, detail=f"Task not found: {taskId}")
    
    task = json.loads(task_json)
    return task


@router.get("/logic-db")
async def get_logic_database():
    """
    获取逻辑库（所有已学习的逻辑规则）
    
    Returns:
        {
            "chapterRules": [...],
            "globalRules": [...],
            "totalRules": int
        }
    """
    try:
        # 获取章节级规则
        chapter_rules = db.query(
            """
            SELECT 'structure' as rule_type, id, chapter_id, rule_content,
                   COALESCE(priority, 1.0)::float as confidence, created_at
            FROM chapter_structure_rules WHERE is_active = TRUE
            UNION ALL
            SELECT 'content' as rule_type, id, chapter_id, rule_content,
                   COALESCE(priority, 1.0)::float as confidence, created_at
            FROM chapter_content_rules WHERE is_active = TRUE
            UNION ALL
            SELECT 'mandatory' as rule_type, id, chapter_id, rule_content,
                   CASE 
                       WHEN priority ~ '^[0-9]+(\\.[0-9]+)?$' THEN priority::numeric
                       ELSE 1.0
                   END as confidence,
                   created_at
            FROM chapter_mandatory_rules WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
        
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
    
    except Exception as e:
        logger.error(f"Failed to fetch logic database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch logic database: {str(e)}")


async def process_learning_task(task_id: str, request: LearningStartRequest):
    """
    后台处理学习任务
    
    使用Redis缓存存储任务状态
    """
    try:
        # 更新进度到Redis
        task_json = await cache.get(f"learning_task:{task_id}")
        if task_json:
            task_status = json.loads(task_json)
            task_status["progress"] = 30
            task_status["message"] = "Processing files..."
            await cache.set(
                f"learning_task:{task_id}",
                json.dumps(task_status),
                ttl=TASK_STATUS_TTL
            )
        
        # TODO: 实际的学习逻辑
        # 1. 解析文件
        # 2. 提取章节
        # 3. 学习逻辑规则
        # 4. 保存到数据库
        
        # 模拟处理
        import asyncio
        await asyncio.sleep(2)  # 模拟耗时操作
        
        # 更新为完成状态
        task_json = await cache.get(f"learning_task:{task_id}")
        if task_json:
            task_status = json.loads(task_json)
            task_status.update({
                "status": "completed",
                "progress": 100,
                "message": "Learning completed successfully",
                "completedAt": datetime.utcnow().isoformat(),
                "result": {
                    "rulesLearned": 15,
                    "chaptersProcessed": 5
                }
            })
            await cache.set(
                f"learning_task:{task_id}",
                json.dumps(task_status),
                ttl=TASK_STATUS_TTL
            )
        
        logger.info(f"Learning task completed: {task_id}")
    
    except Exception as e:
        logger.error(f"Learning task failed: {task_id}, error: {str(e)}")
        task_json = await cache.get(f"learning_task:{task_id}")
        if task_json:
            task_status = json.loads(task_json)
            task_status.update({
                "status": "failed",
                "message": f"Learning failed: {str(e)}",
                "error": str(e)
            })
            await cache.set(
                f"learning_task:{task_id}",
                json.dumps(task_status),
                ttl=TASK_STATUS_TTL
            )


# ========== 章节级学习 ==========

@router.post("/chapter/learn")
async def learn_chapter_pair(request: ChapterPairRequest):
    """
    学习章节对,生成章节逻辑包
    
    Body:
        {
            "tender_chapter_id": "uuid",
            "proposal_chapter_id": "uuid",
            "boq_data": {...},  // 可选
            "custom_rules": [...]  // 可选
        }
    
    Returns:
        {status, logic_package}
    """
    # 1. 获取招标章节
    tender_chapter = db.query_one(
        "SELECT * FROM chapters WHERE id = %s",
        (request.tender_chapter_id,)
    )
    if not tender_chapter:
        raise HTTPException(status_code=404, detail="招标章节不存在")
    
    # 2. 获取投标章节
    proposal_chapter = db.query_one(
        "SELECT * FROM chapters WHERE id = %s",
        (request.proposal_chapter_id,)
    )
    if not proposal_chapter:
        raise HTTPException(status_code=404, detail="投标章节不存在")
    
    # 3. 执行学习
    try:
        logic_package = chapter_engine.learn_chapter(
            tender_chapter=tender_chapter,
            proposal_chapter=proposal_chapter,
            boq=request.boq_data,
            custom_rules=request.custom_rules
        )
        
        return {
            "status": "success",
            "logic_package": logic_package
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节学习失败: {str(e)}")


@router.get("/chapter/{chapter_id}/rules")
async def get_chapter_rules(chapter_id: str):
    """
    获取章节的所有逻辑规则
    
    Args:
        chapter_id: 章节ID
    
    Returns:
        {structure_rules, content_rules, mandatory_rules, scoring_rules, ...}
    """
    # 检查章节是否存在
    chapter = db.query_one(
        "SELECT * FROM chapters WHERE id = %s",
        (chapter_id,)
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 获取各类规则
    structure_rules = db.query(
        "SELECT * FROM chapter_structure_rules WHERE chapter_id = %s AND is_active = TRUE",
        (chapter_id,)
    )
    
    content_rules = db.query(
        "SELECT * FROM chapter_content_rules WHERE chapter_id = %s AND is_active = TRUE",
        (chapter_id,)
    )
    
    mandatory_rules = db.query(
        "SELECT * FROM chapter_mandatory_rules WHERE chapter_id = %s AND is_active = TRUE",
        (chapter_id,)
    )
    
    scoring_rules = db.query(
        "SELECT * FROM chapter_scoring_rules WHERE chapter_id = %s AND is_active = TRUE",
        (chapter_id,)
    )
    
    boq_rules = db.query(
        "SELECT * FROM chapter_boq_rules WHERE chapter_id = %s",
        (chapter_id,)
    )
    
    custom_rules = db.query(
        "SELECT * FROM chapter_custom_rules WHERE chapter_id = %s AND is_active = TRUE",
        (chapter_id,)
    )
    
    return {
        "chapter_id": chapter_id,
        "structure_rules": structure_rules,
        "content_rules": content_rules,
        "mandatory_rules": mandatory_rules,
        "scoring_rules": scoring_rules,
        "boq_rules": boq_rules,
        "custom_rules": custom_rules
    }


# ========== 全局级学习 ==========

@router.post("/global/learn")
async def learn_file_pair(request: FilePairRequest):
    """
    学习文件对,生成全局逻辑包
    
    Body:
        {
            "tender_file_id": "uuid",
            "proposal_file_id": "uuid"
        }
    
    Returns:
        {status, global_package}
    """
    # 1. 获取招标文件及章节
    tender_doc = db.query_one(
        "SELECT * FROM files WHERE id = %s",
        (request.tender_file_id,)
    )
    if not tender_doc:
        raise HTTPException(status_code=404, detail="招标文件不存在")
    
    tender_chapters = db.query(
        "SELECT * FROM chapters WHERE file_id = %s ORDER BY position_order",
        (request.tender_file_id,)
    )
    tender_doc['chapters'] = tender_chapters
    
    # 2. 获取投标文件及章节
    proposal_doc = db.query_one(
        "SELECT * FROM files WHERE id = %s",
        (request.proposal_file_id,)
    )
    if not proposal_doc:
        raise HTTPException(status_code=404, detail="投标文件不存在")
    
    proposal_chapters = db.query(
        "SELECT * FROM chapters WHERE file_id = %s ORDER BY position_order",
        (request.proposal_file_id,)
    )
    proposal_doc['chapters'] = proposal_chapters
    
    # 3. 获取所有章节逻辑包(简化版)
    chapter_packages = []
    for tender_ch in tender_chapters:
        # 这里简化处理,实际应根据chapter_mappings获取对应的proposal章节
        chapter_packages.append({
            'chapter_id': tender_ch['id'],
            'scoring_rules': db.query(
                "SELECT * FROM chapter_scoring_rules WHERE chapter_id = %s",
                (tender_ch['id'],)
            )
        })
    
    # 4. 执行全局学习
    try:
        global_package = global_engine.learn_global(
            tender_doc=tender_doc,
            proposal_doc=proposal_doc,
            chapter_packages=chapter_packages
        )
        
        return {
            "status": "success",
            "global_package": global_package
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"全局学习失败: {str(e)}")


@router.get("/global/{tender_id}/rules")
async def get_global_rules(tender_id: str):
    """
    获取文件的全局逻辑规则
    
    Args:
        tender_id: 招标文件ID
    
    Returns:
        {structure_rules, content_rules, consistency_rules, scoring_rules}
    """
    # 检查文件是否存在
    file = db.query_one(
        "SELECT * FROM files WHERE id = %s",
        (tender_id,)
    )
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 获取各类全局规则
    structure_rules = db.query(
        "SELECT * FROM global_structure_rules WHERE tender_file_id = %s AND is_active = TRUE",
        (tender_id,)
    )
    
    content_rules = db.query(
        "SELECT * FROM global_content_rules WHERE tender_file_id = %s AND is_active = TRUE",
        (tender_id,)
    )
    
    consistency_rules = db.query(
        "SELECT * FROM global_consistency_rules WHERE tender_file_id = %s AND is_active = TRUE",
        (tender_id,)
    )
    
    scoring_rules = db.query(
        "SELECT * FROM global_scoring_rules WHERE tender_file_id = %s AND is_active = TRUE",
        (tender_id,)
    )
    
    return {
        "tender_id": tender_id,
        "structure_rules": structure_rules,
        "content_rules": content_rules,
        "consistency_rules": consistency_rules,
        "scoring_rules": scoring_rules
    }
