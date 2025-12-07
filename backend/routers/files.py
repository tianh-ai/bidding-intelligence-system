"""
文件管理路由
提供文件上传、解析、查询等功能
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from typing import List, Optional
import hashlib
import uuid
import os
import shutil
import json
from engines import ParseEngine
from database import db
from core.config import get_settings
from core.logger import logger

# router and engines
router = APIRouter()
parse_engine = ParseEngine()
settings = get_settings()

# 使用配置系统中的上传路径
UPLOAD_DIR = getattr(settings, 'upload_path', os.getenv('UPLOAD_DIR', './uploads'))
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger.info(f"File upload directory: {UPLOAD_DIR}")

# 确保uploaded_files表存在并包含sha256列（兼容旧schema）
try:
    db.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id uuid PRIMARY KEY,
            filename text NOT NULL,
            filetype text NOT NULL,
            doc_type text NOT NULL DEFAULT 'other',
            file_path text NOT NULL,
            file_size bigint DEFAULT 0,
            sha256 text DEFAULT NULL,
            created_at timestamptz DEFAULT now()
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_files_doc_type ON uploaded_files(doc_type)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_files_created_at ON uploaded_files(created_at DESC)")
    # 兼容性：若表存在但缺少sha256列，则增加该列
    try:
        db.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS sha256 text")
    except Exception:
        pass
except Exception as e:
    print(f"Warning: Could not create or migrate uploaded_files table: {e}")


@router.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    doc_type: Optional[str] = Form("other"),
    overwrite: Optional[bool] = Form(False)
):
    """
    批量上传文件
    
    Args:
        files: 上传的文件列表(PDF/Word)
        doc_type: 文档类型(tender/proposal/reference/other)，默认为other
    
    Returns:
        {totalFiles, files: [...], matchedPairs, unmatchedFiles, duplicates: [...], parsed: [...]}
    """
    # 验证doc_type
    if doc_type not in ['tender', 'proposal', 'reference', 'other']:
        doc_type = 'other'
    
    uploaded_files = []
    failed_files = []
    duplicate_files = []
    parsed_files = []
    
    for file in files:
        # 验证文件类型
        if not file.filename.endswith(('.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt')):
            failed_files.append({"name": file.filename, "error": "不支持的文件格式"})
            continue
        
        # 读取并计算 SHA256（用于稳健判重）
        file_content = await file.read()
        await file.seek(0)  # 重置文件指针
        file_size = len(file_content)
        sha256 = hashlib.sha256(file_content).hexdigest()

        # 检查数据库中是否已存在相同文件（基于 sha256）
        existing = db.query_one(
            "SELECT * FROM uploaded_files WHERE sha256 = %s",
            (sha256,)
        )

        if existing and not overwrite:
            duplicate_files.append({
                "name": file.filename,
                "size": file_size,
                "existing_id": existing['id'],
                "message": f"文件已存在，上传于 {existing.get('created_at')}",
                "sha256": sha256
            })
            # 前端可以决定是否覆盖（通过再次上传并传递 overwrite=true）
            continue

        if existing and overwrite:
            # 删除旧记录及文件（保守删除：uploaded_files + files + chapters）
            try:
                old_id = existing['id']
                old_path = existing.get('file_path')
                db.execute("DELETE FROM uploaded_files WHERE id = %s", (old_id,))
                db.execute("DELETE FROM files WHERE id = %s", (old_id,))
                db.execute("DELETE FROM chapters WHERE file_id = %s", (old_id,))
                if old_path and os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                logger.warning(f"Failed to remove existing file record: {e}")
        
        # 保存文件
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        save_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
        
        try:
            with open(save_path, "wb") as buffer:
                buffer.write(file_content)

            # 保存文件记录到数据库（包含 sha256）
            try:
                db.execute(
                    """
                    INSERT INTO uploaded_files (id, filename, filetype, doc_type, file_path, file_size, sha256, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (file_id, file.filename, file_ext[1:], doc_type, save_path, file_size, sha256)
                )

                uploaded_files.append({
                    "id": file_id,
                    "name": file.filename,
                    "type": doc_type,
                    "size": file_size,
                    "path": save_path
                })

                # 将解析工作交给后台任务（非阻塞）
                try:
                    logger.info(f"Scheduling parse task for file: {file.filename}")
                    # 将解析任务添加到 background tasks
                    background_tasks.add_task(
                        parse_and_store,
                        file_id,
                        save_path,
                        file.filename,
                        doc_type
                    )

                    parsed_files.append({
                        "id": file_id,
                        "name": file.filename,
                        "status": "parsing_scheduled"
                    })

                except Exception as parse_error:
                    logger.error(f"Failed to schedule parse for {file.filename}: {parse_error}")
                    # 解析调度失败不影响上传

            except Exception as db_error:
                logger.error(f"Database error for file {file.filename}: {db_error}")
                # 删除已上传文件
                if os.path.exists(save_path):
                    os.remove(save_path)
                failed_files.append({"name": file.filename, "error": f"数据库错误: {str(db_error)}"})
                continue
                
        except Exception as e:
            logger.error(f"Upload error for file {file.filename}: {e}")
            # 删除已上传文件
            if os.path.exists(save_path):
                os.remove(save_path)
            failed_files.append({"name": file.filename, "error": str(e)})
    
    return {
        "status": "success",
        "totalFiles": len(uploaded_files),
        "files": uploaded_files,
        "matchedPairs": 0,  # 后续实现文件匹配逻辑
        "unmatchedFiles": [f["name"] for f in failed_files],
        "failed": failed_files,
        "duplicates": duplicate_files,  # 重复文件列表
        "parsed": parsed_files  # 解析任务已调度或完成的文件列表
    }


def parse_and_store(file_id: str, save_path: str, filename: str, doc_type: str):
    """
    后台解析任务：解析文件并写入 files 与 chapters 表
    """
    try:
        logger.info(f"Background parse start: {filename}")
        parsed_result = parse_engine.parse(save_path, doc_type)

        # 保存解析结果到 files 表
        try:
            db.execute(
                """
                INSERT INTO files (id, filename, filepath, doc_type, content, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (file_id, filename, save_path, doc_type, parsed_result.get('content', ''))
            )

            # 保存章节结构
            chapters = parsed_result.get('chapters', [])
            for idx, chapter in enumerate(chapters):
                chapter_id = str(uuid.uuid4())
                db.execute(
                    """
                    INSERT INTO chapters (id, file_id, chapter_number, chapter_title, chapter_level, content, position_order, structure_data, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        chapter_id,
                        file_id,
                        chapter.get('chapter_number', str(idx+1)),
                        chapter.get('chapter_title', chapter.get('title', f'第{idx+1}章')),
                        chapter.get('chapter_level', chapter.get('level', 1)),
                        chapter.get('content', ''),
                        idx + 1,
                        json.dumps(chapter.get('structure', {})) if isinstance(chapter.get('structure', {}), dict) else json.dumps({})
                    )
                )

            logger.info(f"Background parse completed: {filename}, chapters={len(chapters)}")
        except Exception as db_err:
            logger.error(f"Error saving parsed result for {filename}: {db_err}")
    except Exception as e:
        logger.error(f"Parse error in background for {filename}: {e}")


@router.get("")
async def get_files(
    doc_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    获取文件列表（前端兼容路由）
    
    Args:
        doc_type: 文档类型过滤(可选)
        limit: 返回数量限制
        offset: 偏移量
    """
    return await get_file_list(doc_type, limit, offset)


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
    try:
        if doc_type:
            query = """
                SELECT id, filename as name, filetype as type, doc_type, 
                       file_size as size, created_at as "uploadedAt"
                FROM uploaded_files
                WHERE doc_type = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (doc_type, limit, offset)
        else:
            query = """
                SELECT id, filename as name, filetype as type, doc_type, 
                       file_size as size, created_at as "uploadedAt"
                FROM uploaded_files
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (limit, offset)
        
        files = db.query(query, params) or []
        
        # 格式化返回数据
        formatted_files = []
        for f in files:
            formatted_files.append({
                "id": f.get("id"),
                "name": f.get("name"),
                "type": f.get("doc_type", "other"),
                "size": f.get("size", 0),
                "uploadedAt": str(f.get("uploadedAt", ""))
            })
        
        return {
            "status": "success",
            "files": formatted_files,
            "total": len(formatted_files)
        }
    except Exception as e:
        return {
            "status": "success",
            "files": [],
            "total": 0
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


@router.delete("/uploaded/{file_id}")
async def delete_uploaded_file(file_id: str):
    """
    删除上传的文件（uploaded_files表）
    
    Args:
        file_id: 文件ID
    """
    # 检查文件是否存在
    file = db.query_one(
        "SELECT * FROM uploaded_files WHERE id = %s",
        (file_id,)
    )
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 删除物理文件
    if file['file_path'] and os.path.exists(file['file_path']):
        try:
            os.remove(file['file_path'])
        except Exception as e:
            logger.warning(f"Failed to delete physical file: {e}")
    
    # 删除数据库记录
    db.execute("DELETE FROM uploaded_files WHERE id = %s", (file_id,))
    
    return {"status": "success", "message": "文件已删除"}


@router.get("/uploaded/{file_id}/download")
async def download_uploaded_file(file_id: str):
    """
    下载上传的文件（uploaded_files表）
    
    Args:
        file_id: 文件ID
    """
    from fastapi.responses import FileResponse
    
    # 检查文件是否存在
    file = db.query_one(
        "SELECT * FROM uploaded_files WHERE id = %s",
        (file_id,)
    )
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = file['file_path']
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件物理路径不存在")
    
    return FileResponse(
        path=file_path,
        filename=file['filename'],
        media_type='application/octet-stream'
    )
