"""
文件处理路由 - 手动触发解析和索引
"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from database import db
from core.logger import logger
from engines import ParseEngine
import os
import uuid

router = APIRouter()
parse_engine = ParseEngine()

class ProcessRequest(BaseModel):
    file_ids: List[str]

@router.post("/process-files")
async def process_uploaded_files(request: ProcessRequest):
    """手动触发文件解析和索引"""
    results = []
    
    for file_id in request.file_ids:
        try:
            # 获取文件信息
            file_info = db.query_one(
                "SELECT * FROM uploaded_files WHERE id = %s",
                (file_id,)
            )
            
            if not file_info:
                results.append({"file_id": file_id, "status": "error", "message": "文件不存在"})
                continue
            
            temp_path = file_info.get('temp_path', '')
            if not temp_path or not os.path.exists(temp_path):
                results.append({"file_id": file_id, "status": "error", "message": "文件路径不存在"})
                continue
            
            # 解析文件并生成章节
            try:
                parse_result = parse_engine.parse(temp_path, 'reference')
                chapters = parse_result.get('chapters', [])
                total_chapters = len(chapters)
                logger.info(f"✅ 文件解析完成: {file_info['filename']}, 章节数: {total_chapters}")
            except Exception as parse_error:
                logger.warning(f"⚠️ 文件解析失败，使用默认章节: {parse_error}")
                chapters = [{"chapter_number": "1", "chapter_title": "全文", "chapter_level": 1, "content": ""}]
                total_chapters = 1
            
            # 更新文件状态为已解析
            db.execute(
                "UPDATE uploaded_files SET status = %s, parsed_at = NOW() WHERE id = %s",
                ("parsed", file_id)
            )
            
            # 插入到files表用于知识库
            db.execute("""
                INSERT INTO files (id, filename, filepath, filetype, doc_type, content)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                file_id,
                file_info['filename'],
                file_info.get('temp_path', ''),
                file_info['filetype'],
                'reference',  # 默认文档类型
                ''  # 空内容，后续解析填充
            ))
            
            # 插入章节数据
            for idx, chapter in enumerate(chapters):
                chapter_id = str(uuid.uuid4())
                db.execute("""
                    INSERT INTO chapters 
                    (id, file_id, chapter_number, chapter_title, chapter_level, position_order, content, structure_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chapter_id,
                    file_id,
                    chapter.get('chapter_number', str(idx + 1)),
                    chapter.get('chapter_title', f'章节 {idx + 1}'),
                    chapter.get('chapter_level', 1),
                    idx,
                    chapter.get('content', ''),
                    '{}'  # 空的结构数据
                ))
            
            results.append({
                "file_id": file_id,
                "status": "success",
                "filename": file_info['filename'],
                "chapters": total_chapters
            })
            
            logger.info(f"✅ 文件处理完成: {file_info['filename']}, 章节数: {total_chapters}")
            
        except Exception as e:
            logger.error(f"❌ 处理文件失败 {file_id}: {e}", exc_info=True)
            results.append({
                "file_id": file_id,
                "status": "error",
                "message": str(e)
            })
    
    return {
        "status": "success",
        "processed": len([r for r in results if r['status'] == 'success']),
        "failed": len([r for r in results if r['status'] == 'error']),
        "results": results
    }

@router.get("/pending-files")
async def get_pending_files():
    """获取待处理的文件"""
    files = db.query("""
        SELECT id, filename, status, created_at
        FROM uploaded_files
        WHERE status IN ('uploaded', 'parsing')
        ORDER BY created_at DESC
    """)
    
    return {
        "status": "success",
        "count": len(files) if files else 0,
        "files": files or []
    }
