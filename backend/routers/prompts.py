"""
提示词管理路由
提供提示词模板的CRUD操作和分类管理
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from core.logger import logger
from database.connection import db

router = APIRouter(prefix="/api/prompts", tags=["提示词"])

# ========== Pydantic Models ==========

class PromptTemplate(BaseModel):
    """提示词模板"""
    id: str
    title: str
    content: str
    category: str  # 分类：文档分析、逻辑提取、内容生成等
    description: Optional[str] = None
    is_public: bool = True
    created_by: Optional[str] = None
    created_at: str
    updated_at: str

class PromptCreate(BaseModel):
    """创建提示词"""
    title: str
    content: str
    category: str
    description: Optional[str] = None
    is_public: bool = True

class PromptUpdate(BaseModel):
    """更新提示词"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

# ========== 内置提示词模板 ==========

BUILTIN_PROMPTS = [
    {
        "id": "analyze-tender",
        "title": "招标文件分析",
        "content": "请分析以下招标文件，提取关键信息：\n\n1. 项目概况\n2. 资质要求\n3. 技术规格\n4. 评分标准\n5. 时间要求\n\n文件内容：\n{document}",
        "category": "文档分析",
        "description": "用于分析招标文件的结构化提示词",
        "is_public": True,
    },
    {
        "id": "extract-logic",
        "title": "逻辑规则提取",
        "content": "请从以下文档中提取业务逻辑规则：\n\n- 必须满足的条件\n- 可选项\n- 计算公式\n- 验证规则\n\n文档：\n{document}",
        "category": "逻辑提取",
        "description": "提取文档中的业务逻辑和规则",
        "is_public": True,
    },
    {
        "id": "generate-proposal",
        "title": "投标文件生成",
        "content": "根据以下招标要求和我方资料，生成投标文件：\n\n招标要求：\n{requirements}\n\n我方资料：\n{our_data}\n\n请生成规范的投标文件，包括：\n1. 公司介绍\n2. 技术方案\n3. 人员配置\n4. 实施计划\n5. 报价说明",
        "category": "内容生成",
        "description": "自动生成投标文件内容",
        "is_public": True,
    },
    {
        "id": "validate-content",
        "title": "内容合规性检查",
        "content": "请检查以下内容是否符合招标要求：\n\n招标要求：\n{requirements}\n\n我方内容：\n{content}\n\n请指出：\n1. 符合的项目\n2. 不符合的项目\n3. 改进建议",
        "category": "验证检查",
        "description": "验证投标内容的合规性",
        "is_public": True,
    },
]

# ========== Helper Functions ==========

def ensure_prompts_table():
    """确保提示词表存在"""
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id text PRIMARY KEY,
                title text NOT NULL,
                content text NOT NULL,
                category text NOT NULL,
                description text,
                is_public boolean DEFAULT true,
                created_by text,
                created_at timestamptz DEFAULT NOW(),
                updated_at timestamptz DEFAULT NOW(),
                deleted_at timestamptz
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompt_templates(category) WHERE deleted_at IS NULL")
    except Exception as e:
        logger.warning(f"Could not create prompt_templates table: {e}")

ensure_prompts_table()

# ========== API Endpoints ==========

@router.get("/templates", response_model=List[PromptTemplate])
async def list_templates(category: Optional[str] = None):
    """
    获取提示词模板列表
    """
    # 返回内置模板
    templates = []
    
    for prompt in BUILTIN_PROMPTS:
        if category is None or prompt["category"] == category:
            templates.append(PromptTemplate(
                id=prompt["id"],
                title=prompt["title"],
                content=prompt["content"],
                category=prompt["category"],
                description=prompt.get("description"),
                is_public=prompt["is_public"],
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            ))
    
    # TODO: 从数据库加载自定义模板
    try:
        query = "SELECT * FROM prompt_templates WHERE deleted_at IS NULL"
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        custom_prompts = db.query(query, params) if params else db.query(query)
        
        for prompt in custom_prompts:
            templates.append(PromptTemplate(**prompt))
    except Exception as e:
        logger.warning(f"Failed to load custom prompts: {e}")
    
    return templates

@router.get("/categories")
async def list_categories():
    """获取所有分类"""
    categories = [
        {"id": "文档分析", "name": "文档分析", "count": 0},
        {"id": "逻辑提取", "name": "逻辑提取", "count": 0},
        {"id": "内容生成", "name": "内容生成", "count": 0},
        {"id": "验证检查", "name": "验证检查", "count": 0},
        {"id": "其他", "name": "其他", "count": 0},
    ]
    
    # 统计每个分类的数量
    for cat in categories:
        cat["count"] = sum(1 for p in BUILTIN_PROMPTS if p["category"] == cat["id"])
    
    return categories

@router.post("/templates", response_model=PromptTemplate)
async def create_template(request: PromptCreate):
    """创建提示词模板"""
    template_id = f"custom-{uuid.uuid4().hex[:8]}"
    
    try:
        db.execute("""
            INSERT INTO prompt_templates (id, title, content, category, description, is_public, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (template_id, request.title, request.content, request.category, request.description, request.is_public))
        
        logger.info(f"Created prompt template: {request.title}")
        
        return PromptTemplate(
            id=template_id,
            title=request.title,
            content=request.content,
            category=request.category,
            description=request.description,
            is_public=request.is_public,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to create prompt template: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.put("/templates/{template_id}", response_model=PromptTemplate)
async def update_template(template_id: str, request: PromptUpdate):
    """更新提示词模板"""
    # 不允许修改内置模板
    if not template_id.startswith("custom-"):
        raise HTTPException(status_code=400, detail="不能修改内置模板")
    
    try:
        updates = []
        params = []
        
        if request.title is not None:
            updates.append("title = %s")
            params.append(request.title)
        if request.content is not None:
            updates.append("content = %s")
            params.append(request.content)
        if request.category is not None:
            updates.append("category = %s")
            params.append(request.category)
        if request.description is not None:
            updates.append("description = %s")
            params.append(request.description)
        if request.is_public is not None:
            updates.append("is_public = %s")
            params.append(request.is_public)
        
        if not updates:
            raise HTTPException(status_code=400, detail="没有要更新的字段")
        
        updates.append("updated_at = NOW()")
        params.append(template_id)
        
        query = f"UPDATE prompt_templates SET {', '.join(updates)} WHERE id = %s RETURNING *"
        result = db.query(query, params)
        
        if not result:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        return PromptTemplate(**result[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt template: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """删除提示词模板（软删除）"""
    if not template_id.startswith("custom-"):
        raise HTTPException(status_code=400, detail="不能删除内置模板")
    
    try:
        db.execute(
            "UPDATE prompt_templates SET deleted_at = NOW() WHERE id = %s",
            (template_id,)
        )
        return {"message": "删除成功"}
    except Exception as e:
        logger.error(f"Failed to delete prompt template: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
