"""
文件管理路由
提供文件上传、解析、查询等功能
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import uuid
import os
import shutil
from engines import ParseEngine
from database import db

router = APIRouter()
parse_engine = ParseEngine()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    doc_type: str = Form(...)
):
    """
    上传并解析文件
    
    Args:
        file: 上传的文件(PDF/Word)
        doc_type: 文档类型(tender/proposal/reference)
    
    Returns:
        {file_id, filename, total_chapters, chapters}
    """
    # 验证文件类型
    if not file.filename.endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="仅支持PDF和Word文档")
    
    # 验证doc_type
    if doc_type not in ['tender', 'proposal', 'reference']:
        raise HTTPException(status_code=400, detail="doc_type必须是tender/proposal/reference之一")
    
    # 保存文件
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 解析文件
    try:
        result = parse_engine.parse(save_path, doc_type)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        # 删除已上传文件
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")


@router.get("/list")
async def get_file_list(
    doc_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    获取文件列表
    
    Args:
        doc_type: 文档类型过滤(可选)
        limit: 返回数量限制
        offset: 偏移量
    """
    if doc_type:
        query = """
            SELECT id, filename, filetype, doc_type, 
                   metadata, created_at
            FROM files
            WHERE doc_type = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params = (doc_type, limit, offset)
    else:
        query = """
            SELECT id, filename, filetype, doc_type, 
                   metadata, created_at
            FROM files
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params = (limit, offset)
    
    files = db.query(query, params)
    
    # 获取总数
    count_query = "SELECT COUNT(*) as total FROM files"
    if doc_type:
        count_query += " WHERE doc_type = %s"
        total = db.query_one(count_query, (doc_type,))
    else:
        total = db.query_one(count_query)
    
    return {
        "total": total['total'] if total else 0,
        "data": files
    }


@router.get("/{file_id}")
async def get_file_detail(file_id: str):
    """
    获取文件详情(包含章节)
    
    Args:
        file_id: 文件ID
    """
    # 获取文件信息
    file = db.query_one(
        "SELECT * FROM files WHERE id = %s",
        (file_id,)
    )
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 获取章节列表
    chapters = db.query(
        """
        SELECT id, chapter_number, chapter_title, chapter_level, 
               position_order, structure_data
        FROM chapters
        WHERE file_id = %s
        ORDER BY position_order
        """,
        (file_id,)
    )
    
    file['chapters'] = chapters
    return file


@router.get("/{file_id}/chapters")
async def get_chapters(file_id: str):
    """
    获取文件的所有章节
    
    Args:
        file_id: 文件ID
    """
    chapters = db.query(
        "SELECT * FROM chapters WHERE file_id = %s ORDER BY position_order",
        (file_id,)
    )
    
    return {
        "file_id": file_id,
        "total": len(chapters),
        "chapters": chapters
    }


@router.get("/chapter/{chapter_id}")
async def get_chapter_detail(chapter_id: str):
    """
    获取章节详情(包含完整内容)
    
    Args:
        chapter_id: 章节ID
    """
    chapter = db.query_one(
        "SELECT * FROM chapters WHERE id = %s",
        (chapter_id,)
    )
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    return chapter


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    删除文件(及其关联的章节)
    
    Args:
        file_id: 文件ID
    """
    # 检查文件是否存在
    file = db.query_one(
        "SELECT * FROM files WHERE id = %s",
        (file_id,)
    )
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 删除物理文件
    if file['filepath'] and os.path.exists(file['filepath']):
        os.remove(file['filepath'])
    
    # 删除数据库记录(CASCADE会自动删除关联章节)
    db.execute("DELETE FROM files WHERE id = %s", (file_id,))
    
    return {"status": "success", "message": "文件已删除"}
