"""
逻辑学习路由
提供章节级和全局级学习功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from engines import ChapterLogicEngine, GlobalLogicEngine
from database import db

router = APIRouter()
chapter_engine = ChapterLogicEngine()
global_engine = GlobalLogicEngine()


# ========== 请求模型 ==========

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
