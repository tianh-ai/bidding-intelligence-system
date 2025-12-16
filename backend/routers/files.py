"""
文件管理路由
提供文件上传、解析、查询等功能
采用三阶段架构：temp → parsed → archive
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
import hashlib
import uuid
import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
from engines import ParseEngine
from engines.document_classifier import DocumentClassifier
from database import db
from core.config import get_settings
from core.logger import logger
from core.file_status import FileStatus, DuplicateAction, FileCategory

# router and engines
router = APIRouter()
parse_engine = ParseEngine()
document_classifier = DocumentClassifier()
settings = get_settings()

# 使用配置的存储路径（支持本地和容器环境）
UPLOAD_DIR = settings.upload_path
TEMP_DIR = os.path.join(UPLOAD_DIR, "temp")
PARSED_DIR = os.path.join(os.path.dirname(UPLOAD_DIR), "parsed")
ARCHIVE_DIR = os.path.join(os.path.dirname(UPLOAD_DIR), "archive")

# 确保所有目录存在
for directory in [UPLOAD_DIR, TEMP_DIR, PARSED_DIR, ARCHIVE_DIR]:
    os.makedirs(directory, exist_ok=True)

logger.info(f"File upload directories initialized (SSD Storage):")
logger.info(f"  - Upload: {UPLOAD_DIR}")
logger.info(f"  - Temp: {TEMP_DIR}")
logger.info(f"  - Parsed: {PARSED_DIR}")
logger.info(f"  - Archive: {ARCHIVE_DIR}")
logger.info(f"  - Archive: {ARCHIVE_DIR}")

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

    # 兼容性迁移：为表补齐最新代码依赖的列
    column_migrations = [
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS sha256 text",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS status text DEFAULT 'uploaded'",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS uploader text",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS temp_path text",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS duplicate_action text DEFAULT 'skip'",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS original_file_id uuid",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS version integer DEFAULT 1",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS status_updated_at timestamptz",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS parsed_at timestamptz",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS archived_at timestamptz",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS indexed_at timestamptz",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS archive_path text",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS category text DEFAULT 'other'",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS semantic_filename text",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS metadata jsonb",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS error_log text"
    ]

    for migration_sql in column_migrations:
        try:
            db.execute(migration_sql)
        except Exception as migration_error:
            logger.warning(f"uploaded_files列迁移失败: {migration_sql} - {migration_error}")
except Exception as e:
    print(f"Warning: Could not create or migrate uploaded_files table: {e}")


@router.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    uploader: str = Form(...),  # 必填：上传人
    duplicate_action: str = Form(default="skip"),  # overwrite/update/skip
):
    """
    批量上传文件 - 优化的三阶段架构
    
    阶段1: 上传到临时目录 (temp/)
    阶段2: 后台解析并归档 (parsed/ → archive/)
    阶段3: 建立知识库索引
    
    Args:
        files: 上传的文件列表(PDF/Word/Excel/TXT)
        uploader: 上传人姓名（必填）
        duplicate_action: 重复文件处理策略
            - skip: 跳过重复文件（默认）
            - overwrite: 覆盖原文件
            - update: 创建新版本
    
    Returns:
        {
            status: "success",
            session_id: str,
            uploaded: [{id, name, status, ...}],
            duplicates: [{name, sha256, action, existing_id}],
            failed: [{name, error}]
        }
    """
    logger.info(f"📤 收到上传请求 - 文件数: {len(files)}, 上传人: {uploader}, 重复策略: {duplicate_action}")
    
    # 生成session_id用于批量上传
    session_id = str(uuid.uuid4())[:8]
    session_temp_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_temp_dir, exist_ok=True)
    
    uploaded_files = []
    duplicate_files = []
    failed_files = []
    
    for file in files:
        try:
            # 1. 验证文件类型
            if not file.filename.endswith(('.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt')):
                failed_files.append({
                    "name": file.filename,
                    "error": "不支持的文件格式"
                })
                continue
            
            # 2. 读取文件内容并计算哈希
            file_content = await file.read()
            await file.seek(0)
            file_size = len(file_content)
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            
            logger.info(f"  📄 处理文件: {file.filename} (SHA256: {sha256_hash[:16]}...)")
            
            # 3. 检查重复文件
            try:
                existing = db.query_one(
                    "SELECT * FROM uploaded_files WHERE sha256 = %s AND status != %s",
                    (sha256_hash, FileStatus.DELETED)
                )
            except Exception as e:
                logger.error(f"数据库查询错误: {e}")
                try:
                    db.conn.rollback()
                except:
                    pass
                existing = None
            
            if existing:
                logger.info(f"  🔁 发现重复文件: {file.filename}")
                
                if duplicate_action == "skip":
                    # 跳过重复文件
                    duplicate_files.append({
                        "name": file.filename,
                        "sha256": sha256_hash,
                        "action": "skipped",
                        "existing_id": existing['id'],
                        "existing_name": existing.get('semantic_filename') or existing['filename'],
                        "existing_size": existing.get('size', 0),
                        "existing_uploaded_at": existing.get('created_at', '').isoformat() if existing.get('created_at') else None,
                        "message": f"文件已存在，上传于 {existing.get('created_at')}"
                    })
                    continue
                
                elif duplicate_action == "overwrite":
                    # 覆盖：删除旧文件记录
                    logger.info(f"  ♻️  覆盖模式：删除旧记录 {existing['id']}")
                    old_id = existing['id']
                    try:
                        # 删除物理文件
                        for path_col in ['temp_path', 'archive_path']:
                            old_path = existing.get(path_col)
                            if old_path and os.path.exists(old_path):
                                os.remove(old_path)
                        
                        # 删除数据库记录
                        db.execute("DELETE FROM uploaded_files WHERE id = %s", (old_id,))
                        db.execute("DELETE FROM files WHERE id = %s", (old_id,))
                        db.execute("DELETE FROM chapters WHERE file_id = %s", (old_id,))
                        
                    except Exception as e:
                        logger.warning(f"清理旧文件失败: {e}")
                
                elif duplicate_action == "update":
                    # 更新：创建新版本
                    logger.info(f"  📌 更新模式：创建版本 {existing.get('version', 1) + 1}")
                    # 继续处理，但记录原文件ID和版本号
            
            # 4. 生成文件ID并保存到临时目录
            file_id = str(uuid.uuid4())
            file_ext = os.path.splitext(file.filename)[1]
            temp_filename = f"{file_id}{file_ext}"
            temp_path = os.path.join(session_temp_dir, temp_filename)
            
            with open(temp_path, "wb") as buffer:
                buffer.write(file_content)
            
            logger.info(f"  💾 临时保存: {temp_path}")
            
            # 5. 保存到数据库（状态=uploaded）
            try:
                version = 1
                original_file_id = None
                
                if existing and duplicate_action == "update":
                    version = existing.get('version', 1) + 1
                    original_file_id = existing['id']
                
                db.execute(
                    """
                    INSERT INTO uploaded_files (
                        id, filename, filetype, file_path, file_size, sha256,
                        status, uploader, temp_path, duplicate_action, 
                        original_file_id, version, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        file_id, file.filename, file_ext[1:], temp_path, file_size, sha256_hash,
                        FileStatus.UPLOADED, uploader, temp_path, duplicate_action,
                        original_file_id, version
                    )
                )
                
                uploaded_files.append({
                    "id": file_id,
                    "name": file.filename,
                    "size": file_size,
                    "status": FileStatus.UPLOADED,
                    "temp_path": temp_path,
                    "uploader": uploader,
                    "version": version,
                    "uploaded_at": datetime.now().isoformat()
                })
                
                logger.info(f"  ✅ 数据库记录已创建: {file_id}")
                
                # 6. 添加后台解析任务
                background_tasks.add_task(
                    parse_and_archive_file,
                    file_id,
                    temp_path,
                    file.filename
                )
                logger.info(f"  ⚙️  后台解析任务已调度")
                
            except Exception as db_error:
                logger.error(f"数据库写入失败: {db_error}")
                try:
                    db.conn.rollback()
                except:
                    pass
                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                failed_files.append({
                    "name": file.filename,
                    "error": f"数据库错误: {str(db_error)}"
                })
                continue
        
        except Exception as e:
            logger.error(f"处理文件 {file.filename} 失败: {e}", exc_info=True)
            failed_files.append({
                "name": file.filename,
                "error": str(e)
            })
    
    logger.info(f"📊 上传完成 - 成功: {len(uploaded_files)}, 重复: {len(duplicate_files)}, 失败: {len(failed_files)}")
    
    return {
        "status": "success",
        "session_id": session_id,
        "uploaded": uploaded_files,
        "duplicates": duplicate_files,
        "failed": failed_files
    }
    
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
        try:
            existing = db.query_one(
                "SELECT * FROM uploaded_files WHERE sha256 = %s",
                (sha256,)
            )
        except Exception as e:
            logger.error(f"Database query error for {file.filename}: {e}")
            # 回滚事务
            try:
                db.conn.rollback()
            except:
                pass
            failed_files.append({"name": file.filename, "error": f"数据库查询错误: {str(e)}"})
            continue

        if existing and not overwrite:
            duplicate_files.append({
                "name": file.filename,
                "size": file_size,
                "existing_id": existing['id'],
                "existing_name": existing.get('semantic_filename') or existing['filename'],
                "existing_size": existing.get('size', file_size),
                "existing_uploaded_at": existing.get('created_at', '').isoformat() if existing.get('created_at') else None,
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
                    "path": save_path,
                    "uploadedAt": datetime.now().isoformat()
                })
                
                logger.info(f"文件已保存到数据库: {file.filename}, ID: {file_id}")

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
                # 回滚事务
                try:
                    db.conn.rollback()
                except:
                    pass
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


def parse_and_archive_file(file_id: str, temp_path: str, filename: str):
    """
    后台任务：解析文件并自动归档
    
    流程：
    1. 更新状态为 PARSING
    2. 解析文件（提取文本、表格、章节）
    3. 智能分类（快速/详细分析）
    4. 归档到 archive/{year}/{month}/{category}/
    5. 删除临时文件
    6. 建立知识库索引
    
    Args:
        file_id: 文件ID
        temp_path: 临时文件路径
        filename: 原始文件名
    """
    try:
        logger.info(f"🔄 开始解析: {filename}")
        
        # 1. 更新状态为PARSING
        try:
            db.execute(
                "UPDATE uploaded_files SET status = %s, status_updated_at = NOW() WHERE id = %s",
                (FileStatus.PARSING, file_id)
            )
        except Exception as e:
            try:
                db.conn.rollback()
            except:
                pass
            raise e
        
        # 2. 解析文件（使用增强的章节内容提取器）
        allowed_doc_types = {"tender", "proposal", "reference"}
        default_doc_type = "reference"
        
        # 使用增强的解析引擎（包含章节内容和格式提取）
        try:
            from engines.chapter_content_extractor import get_chapter_content_extractor
            from engines.format_extractor import get_format_extractor
            
            # 先用传统方法提取基本内容
            parsed_result = parse_engine.parse(temp_path, default_doc_type, save_to_db=False)
            content = parsed_result.get('content', '')
            
            # 使用增强的章节提取器获取章节内容
            content_extractor = get_chapter_content_extractor(use_ollama=False)
            chapters = content_extractor.extract_chapters_with_content(content)
            
            # 对于DOCX文件，提取格式信息
            format_info = {}
            if temp_path.lower().endswith(('.docx', '.doc')):
                try:
                    format_extractor = get_format_extractor()
                    format_info = format_extractor.extract_format_from_docx(temp_path)
                    
                    # 为每个章节添加格式信息
                    chapter_formats = format_extractor.extract_chapter_formats(temp_path, chapters)
                    for i, ch in enumerate(chapters):
                        if i < len(chapter_formats):
                            ch['structure_data'] = chapter_formats[i]
                    
                    logger.info(f"  ✅ 增强解析器: {len(chapters)} 章节, 格式信息已提取")
                except Exception as fmt_error:
                    logger.warning(f"  ⚠️  格式提取失败: {fmt_error}")
            else:
                logger.info(f"  ✅ 增强解析器: {len(chapters)} 章节（非DOCX，无格式信息）")
            
        except Exception as parse_error:
            logger.warning(f"  ⚠️  增强解析器失败，回退到传统解析: {parse_error}")
            # 回退到传统方法
            parsed_result = parse_engine.parse(temp_path, default_doc_type, save_to_db=False)
            content = parsed_result.get('content', '')
            chapters = parsed_result.get('chapters', [])
            format_info = {}
        
        # 提取元数据
        metadata = {
            "original_filename": filename,  # 保存原始文件名
            "chapters": [
                {
                    "title": ch.get('title', ''),
                    "level": ch.get('level', 1),
                    "page": ch.get('page', 0)
                }
                for ch in chapters
            ],
            "page_count": len(chapters),
            "has_tables": bool(parsed_result.get('tables')),
            "parse_time": datetime.now().isoformat()
        }
        
        logger.info(f"  📝 解析完成: {len(chapters)} 个章节")
        
        # 3. 更新状态为PARSED并保存元数据
        try:
            db.execute(
                """
                UPDATE uploaded_files 
                SET status = %s, parsed_at = NOW(), metadata = %s
                WHERE id = %s
                """,
                (FileStatus.PARSED, json.dumps(metadata), file_id)
            )
        except Exception as e:
            try:
                db.conn.rollback()
            except:
                pass
            raise e
        
        # 4. 智能分类
        category, semantic_filename = document_classifier.classify(
            filename,
            metadata,
            content
        )

        # 统一分类，确保符合 files.doc_type 检查约束
        safe_category = category if category in allowed_doc_types else default_doc_type
        
        logger.info(f"  🏷️  分类: {category}, 语义名: {semantic_filename}")
        
        # 5. 生成归档路径
        file_ext = os.path.splitext(filename)[1][1:] if '.' in filename else 'txt'
        now = datetime.now()
        year = now.year
        month = now.month
        archive_dir = os.path.join(ARCHIVE_DIR, str(year), f"{month:02d}", safe_category)
        os.makedirs(archive_dir, exist_ok=True)
        
        archive_path = os.path.join(archive_dir, semantic_filename)
        
        # 6. 移动文件到归档目录
        try:
            db.execute(
                "UPDATE uploaded_files SET status = %s WHERE id = %s",
                (FileStatus.ARCHIVING, file_id)
            )
        except Exception as e:
            try:
                db.conn.rollback()
            except:
                pass
            raise e
        
        shutil.copy2(temp_path, archive_path)
        logger.info(f"  📦 归档到: {archive_path}")
        
        # 7. 更新数据库
        try:
            db.execute(
                """
                UPDATE uploaded_files 
                SET status = %s, archive_path = %s, category = %s, 
                    semantic_filename = %s, archived_at = NOW(), file_path = %s
                WHERE id = %s
                """,
                (FileStatus.ARCHIVED, archive_path, safe_category, semantic_filename, archive_path, file_id)
            )
        except Exception as e:
            try:
                db.conn.rollback()
            except:
                pass
            raise e
        
        # 8. 保存到files表（用于知识库）
        try:
            db.execute(
                """
                INSERT INTO files (id, filename, filepath, filetype, doc_type, content, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content, filetype = EXCLUDED.filetype, doc_type = EXCLUDED.doc_type
                """,
                (file_id, semantic_filename, archive_path, file_ext, safe_category, content)
            )
            
            # 保存章节（包含content和structure_data）
            logger.info(f"  📊 章节数据样例: {chapters[:2] if chapters else '无'}")
            for idx, chapter in enumerate(chapters):
                chapter_id = str(uuid.uuid4())
                
                # 清理标题：去除目录点号和页码
                raw_title = chapter.get('chapter_title', chapter.get('title', f'第{idx+1}章'))
                # 去除"...数字"格式的页码标记
                import re
                clean_title = re.sub(r'[\.。\s]+\d+$', '', raw_title)  # 去除尾部的 "...123"
                clean_title = re.sub(r'[\.。]{3,}', '', clean_title)  # 去除连续点号
                clean_title = clean_title.strip()
                
                # 获取章节内容和格式信息
                chapter_content = chapter.get('content', '')
                structure_data = chapter.get('structure_data', {})
                
                # 如果structure_data是dict，转为JSON
                if isinstance(structure_data, dict):
                    structure_data_json = json.dumps(structure_data, ensure_ascii=False)
                else:
                    structure_data_json = '{}'
                
                db.execute(
                    """
                    INSERT INTO chapters (
                        id, file_id, chapter_number, chapter_title, 
                        chapter_level, content, position_order, structure_data, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
                    """,
                    (
                        chapter_id, file_id,
                        chapter.get('chapter_number', str(idx+1)),
                        clean_title,
                        chapter.get('chapter_level', chapter.get('level', 1)),
                        chapter_content,  # 现在有内容了！
                        idx + 1,
                        structure_data_json  # 格式信息
                    )
                )
                
            logger.info(f"  📚 知识库记录已保存（包含内容和格式信息）")
            
            logger.info(f"  📚 知识库记录已保存")
            
        except Exception as db_err:
            logger.error(f"保存知识库失败: {db_err}")
            try:
                db.conn.rollback()
            except:
                pass
        
        # 9. 删除临时文件
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                # 尝试删除空的session目录
                session_dir = os.path.dirname(temp_path)
                if os.path.isdir(session_dir) and not os.listdir(session_dir):
                    os.rmdir(session_dir)
                logger.info(f"  🗑️  临时文件已删除")
        except Exception as e:
            logger.warning(f"删除临时文件失败: {e}")
        
        # 10. 向量化并建立知识库索引
        try:
            db.execute(
                "UPDATE uploaded_files SET status = %s WHERE id = %s",
                (FileStatus.INDEXING, file_id)
            )
        except Exception as e:
            try:
                db.conn.rollback()
            except:
                pass
            logger.warning(f"更新索引中状态失败: {e}")
        
        # 提取知识库条目并向量化
        try:
            # 简化版：按章节建立向量索引
            from openai import OpenAI
            openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            for idx, chapter in enumerate(chapters):
                chapter_content = chapter.get('content', '')
                if not chapter_content or len(chapter_content) < 50:
                    continue
                
                # 分块（每1000字符一块）
                chunks = [chapter_content[i:i+1000] for i in range(0, len(chapter_content), 1000)]
                
                for chunk_idx, chunk in enumerate(chunks[:5]):  # 限制每章最多5块
                    try:
                        # 生成向量
                        response = openai_client.embeddings.create(
                            model="text-embedding-3-small",
                            input=chunk
                        )
                        embedding = response.data[0].embedding
                        
                        # 保存到vectors表
                        vector_id = str(uuid.uuid4())
                        db.execute(
                            """
                            INSERT INTO vectors (id, file_id, chunk_type, chunk, embedding, created_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                            """,
                            (vector_id, file_id, 'chapter', chunk, embedding)
                        )
                        
                        logger.info(f"  🔍 向量索引已建立: 章节{idx+1} 块{chunk_idx+1}")
                    except Exception as vec_err:
                        logger.warning(f"向量化失败: {vec_err}")
                        continue
            
            # 提取知识库条目
            extract_knowledge_entries(file_id, semantic_filename, content)
            
        except Exception as index_err:
            logger.warning(f"向量索引建立失败: {index_err}")
        
        # 11. 更新状态为INDEXED
        try:
            db.execute(
                "UPDATE uploaded_files SET status = %s, indexed_at = NOW() WHERE id = %s",
                (FileStatus.INDEXED, file_id)
            )
        except Exception as e:
            try:
                db.conn.rollback()
            except:
                pass
            logger.warning(f"更新索引状态失败: {e}")
        
        logger.info(f"✅ 文件处理完成: {filename} → {semantic_filename}")
        
    except Exception as e:
        logger.error(f"❌ 解析归档失败 {filename}: {e}", exc_info=True)
        # 更新状态为PARSE_FAILED
        try:
            db.execute(
                """
                UPDATE uploaded_files 
                SET status = %s, error_log = %s, status_updated_at = NOW() 
                WHERE id = %s
                """,
                (FileStatus.PARSE_FAILED, str(e), file_id)
            )
        except Exception as update_err:
            try:
                db.conn.rollback()
            except:
                pass
            logger.error(f"更新失败状态失败: {update_err}")


def parse_and_store(file_id: str, save_path: str, filename: str, doc_type: str):
    """
    后台解析任务：解析文件并写入 files 与 chapters 表
    """
    try:
        logger.info(f"Background parse start: {filename}")
        # 传递 file_id 以启用图片提取
        parsed_result = parse_engine.parse(save_path, doc_type, file_id=file_id)

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
    # 兼容旧字段命名: doc_type 对应新的 category
    return await get_file_list(
        category=doc_type,
        limit=limit,
        offset=offset
    )


@router.get("/list")
async def get_file_list(
    status: Optional[str] = None,
    category: Optional[str] = None,
    uploader: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    获取文件列表 - 支持多维度筛选
    
    Args:
        status: 状态过滤(uploaded/parsing/parsed/archived/indexed/failed)
        category: 分类过滤(tender/proposal/contract/report/reference/other)
        uploader: 上传人过滤
        limit: 返回数量限制
        offset: 偏移量
    """
    try:
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if category:
            conditions.append("category = %s")
            params.append(category)
        
        if uploader:
            conditions.append("uploader = %s")
            params.append(uploader)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                id, 
                filename as name, 
                semantic_filename,
                filetype as type, 
                category,
                status,
                file_size as size,
                uploader,
                version,
                archive_path,
                created_at as "uploadedAt",
                parsed_at as "parsedAt",
                archived_at as "archivedAt",
                indexed_at as "indexedAt"
            FROM uploaded_files
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        files = db.query(query, tuple(params)) or []
        
        # 格式化返回数据
        formatted_files = []
        for f in files:
            formatted_files.append({
                "id": f.get("id"),
                "name": f.get("name"),
                "semanticName": f.get("semantic_filename"),
                "type": f.get("type", "other"),
                "category": f.get("category"),
                "status": f.get("status"),
                "size": f.get("size", 0),
                "uploader": f.get("uploader"),
                "version": f.get("version", 1),
                "archivePath": f.get("archive_path"),
                "uploadedAt": str(f.get("uploadedAt", "")),
                "parsedAt": str(f.get("parsedAt", "")) if f.get("parsedAt") else None,
                "archivedAt": str(f.get("archivedAt", "")) if f.get("archivedAt") else None,
                "indexedAt": str(f.get("indexedAt", "")) if f.get("indexedAt") else None,
            })
        
        return {
            "status": "success",
            "files": formatted_files,
            "total": len(formatted_files)
        }
    except Exception as e:
        logger.error(f"查询文件列表失败: {e}", exc_info=True)
        return {
            "status": "success",
            "files": [],
            "total": 0
        }


@router.get("/stats")
async def get_file_stats():
    """
    获取文件统计信息
    
    Returns:
        {
            total_files: int,
            total_size: int,
            by_category: {...},
            by_status: {...},
            recent_uploads: [...]
        }
    """
    try:
        # 总文件数和总大小
        stats_query = """
            SELECT 
                COUNT(*) as total_files,
                COALESCE(SUM(file_size), 0) as total_size
            FROM uploaded_files
        """
        stats = db.query_one(stats_query) or {"total_files": 0, "total_size": 0}
        
        # 按分类统计
        category_stats = db.query("""
            SELECT category, COUNT(*) as count
            FROM uploaded_files
            GROUP BY category
        """) or []
        
        # 按状态统计
        status_stats = db.query("""
            SELECT status, COUNT(*) as count
            FROM uploaded_files
            GROUP BY status
        """) or []
        
        # 最近上传
        recent_uploads = db.query("""
            SELECT filename, category, file_size, created_at
            FROM uploaded_files
            ORDER BY created_at DESC
            LIMIT 5
        """) or []
        
        return {
            "status": "success",
            "total_files": stats.get("total_files", 0),
            "total_size": stats.get("total_size", 0),
            "by_category": {item["category"]: item["count"] for item in category_stats},
            "by_status": {item["status"]: item["count"] for item in status_stats},
            "recent_uploads": [
                {
                    "filename": item["filename"],
                    "category": item["category"],
                    "size": item["file_size"],
                    "uploadedAt": str(item["created_at"])
                }
                for item in recent_uploads
            ]
        }
    except Exception as e:
        logger.error(f"获取文件统计失败: {e}", exc_info=True)
        return {
            "status": "error",
            "total_files": 0,
            "total_size": 0,
            "by_category": {},
            "by_status": {},
            "recent_uploads": []
        }


@router.get("/database-details")
async def get_database_details():
    """
    获取数据库统计信息
    
    Returns:
        {
            totalFiles: int,
            totalSize: int,
            storageUsed: float (MB),
            knowledgeEntries: int,
            lastUpdate: str
        }
    """
    try:
        # 统计文件数量
        total_files_result = db.query_one("SELECT COUNT(*) as count FROM uploaded_files")
        total_files = total_files_result['count'] if total_files_result else 0
        
        # 统计总大小
        total_size_result = db.query_one("SELECT COALESCE(SUM(file_size), 0) as total FROM uploaded_files")
        total_size = total_size_result['total'] if total_size_result else 0
        storage_used_mb = round(total_size / (1024 * 1024), 2)
        
        # 统计知识库条目
        try:
            kb_result = db.query_one("SELECT COUNT(*) as count FROM files")
            kb_count = kb_result['count'] if kb_result else 0
        except:
            kb_count = 0
        
        # 获取最后更新时间
        last_update_result = db.query_one(
            "SELECT MAX(created_at) as last_update FROM uploaded_files"
        )
        last_update = last_update_result['last_update'] if last_update_result and last_update_result['last_update'] else "未知"
        if last_update != "未知":
            last_update = str(last_update)
        
        return {
            "totalFiles": total_files,
            "totalSize": total_size,
            "storageUsed": storage_used_mb,
            "knowledgeEntries": kb_count,
            "lastUpdate": last_update
        }
    except Exception as e:
        logger.error(f"Error getting database details: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据库详情失败: {str(e)}")


@router.get("/knowledge-base-entries")
async def get_knowledge_base_entries():
    """
    获取知识库条目列表
    
    Returns:
        List of knowledge base entries
    """
    try:
        # 从files表查询（作为知识库），JOIN uploaded_files获取原始文件名
        entries = db.query("""
            SELECT 
                f.id,
                COALESCE(uf.filename, f.filename) as title,
                f.doc_type as category,
                COALESCE(uf.filename, f.filename) as "fileName",
                f.created_at as "createdAt",
                COUNT(c.id) as "chapterCount"
            FROM files f
            LEFT JOIN uploaded_files uf ON f.id = uf.id
            LEFT JOIN chapters c ON f.id = c.file_id
            GROUP BY f.id, f.filename, uf.filename, f.doc_type, f.created_at
            ORDER BY f.created_at DESC
            LIMIT 100
        """)
        
        if entries:
            formatted = []
            for entry in entries:
                formatted.append({
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "category": entry.get("category", "reference"),
                    "fileName": entry.get("fileName"),
                    "createdAt": str(entry.get("createdAt", "")),
                    "chapterCount": entry.get("chapterCount", 0)
                })
            return formatted
        
        return []
    except Exception as e:
        logger.error(f"Error getting knowledge base entries: {e}", exc_info=True)
        return []


@router.get("/knowledge-base")
async def get_knowledge_base_alias():
    """兼容旧路径，返回知识库条目列表"""
    return await get_knowledge_base_entries()


@router.get("/document-indexes")
async def get_document_indexes(fileId: Optional[str] = None):
    """
    获取文档索引列表
    
    Args:
        fileId: 可选，指定文件ID（使用驼峰命名匹配前端）
    
    Returns:
        List of document indexes with hierarchical structure
    """
    try:
        def build_chapter_tree(chapter_rows):
            """将平铺的章节列表构建为树结构"""
            roots = []
            stack = []  # 维护每一层的最后节点

            for chapter in chapter_rows:
                level = chapter.get('chapter_level') or 1
                try:
                    level_int = int(level)
                except Exception:
                    level_int = 1

                node = {
                    'number': chapter.get('chapter_number'),
                    'title': chapter.get('chapter_title'),
                    'level': level_int,
                    'pageNum': chapter.get('position_order', 1),
                    'children': []
                }

                # 确保栈深与当前level匹配
                while stack and stack[-1]['level'] >= level_int:
                    stack.pop()

                if stack:
                    stack[-1]['children'].append(node)
                else:
                    roots.append(node)

                stack.append(node)

            return roots

        document_indexes = []
        seen_files = set()  # 防止重复

        # 查询文件和章节信息，JOIN uploaded_files 获取原始文件名
        if fileId:
            files = db.query_all(
                """
                SELECT f.*, uf.filename as original_filename
                FROM files f
                LEFT JOIN uploaded_files uf ON f.id = uf.id
                WHERE f.id = %s
                """,
                (fileId,)
            )
        else:
            # 按创建时间倒序返回最近的文件
            files = db.query_all(
                """
                SELECT f.*, uf.filename as original_filename
                FROM files f
                LEFT JOIN uploaded_files uf ON f.id = uf.id
                ORDER BY f.created_at DESC
                LIMIT 50
                """
            )

        for file in files:
            file_id_str = str(file['id'])

            # 跳过已处理的文件
            if file_id_str in seen_files:
                continue
            seen_files.add(file_id_str)

            # 查询章节
            chapters = db.query_all(
                """
                SELECT chapter_number, chapter_title, chapter_level, position_order
                FROM chapters
                WHERE file_id = %s
                ORDER BY position_order
                """,
                (file['id'],)
            )

            # 只返回有章节的文件
            if not chapters:
                continue

            chapter_tree = build_chapter_tree(chapters)
            
            # 优先使用 JOIN 查询得到的 original_filename（来自 uploaded_files 表）
            # 如果没有，则尝试从 metadata 中获取
            # 最后才使用 files.filename（语义化文件名）
            display_name = file.get('original_filename') or file['filename']
            if not file.get('original_filename') and file.get('metadata') and isinstance(file['metadata'], dict):
                display_name = file['metadata'].get('original_filename', file['filename'])

            document_indexes.append({
                'id': file['id'],
                'fileName': display_name,
                'chapters': chapter_tree
            })
        
        return document_indexes
        
    except Exception as e:
        logger.error(f"Error getting document indexes: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档索引失败: {str(e)}")


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


class ProcessFilesRequest(BaseModel):
    fileIds: List[str]


@router.post("/process")
async def process_files(
    background_tasks: BackgroundTasks,
    request: ProcessFilesRequest
):
    """
    处理上传的文件：生成知识库和文档索引
    
    Args:
        fileIds: 文件ID列表
    
    Returns:
        {
            status: str,
            processedFiles: int,
            documentIndexes: List[DocumentIndex]
        }
    """
    file_ids = request.fileIds
    
    if not file_ids:
        raise HTTPException(status_code=400, detail="未提供文件ID")
    
    try:
        document_indexes = []
        
        for file_id in file_ids:
            # 查询文件信息
            file_info = db.query_one(
                "SELECT * FROM uploaded_files WHERE id = %s",
                (file_id,)
            )
            
            if not file_info:
                logger.warning(f"File not found: {file_id}")
                continue
            
            # 解析文件生成文档索引
            try:
                # 解析文档结构
                parsed_data = parse_engine.parse(file_info['file_path'], file_info['doc_type'])
                
                # 生成章节索引
                chapters = parsed_data.get('chapters', [])
                chapter_index = []
                
                for chapter in chapters:
                    chapter_index.append({
                        'title': chapter.get('chapter_title', chapter.get('title', '未命名章节')),
                        'level': chapter.get('chapter_level', chapter.get('level', 1)),
                        'pageNum': chapter.get('page_number', chapter.get('page', 1)),
                        'children': []  # 可以递归处理子章节
                    })
                
                document_indexes.append({
                    'id': file_id,
                    'fileName': file_info['filename'],
                    'chapters': chapter_index
                })
                
                # 提取知识库条目（后台任务）
                background_tasks.add_task(
                    extract_knowledge_entries,
                    file_id,
                    file_info['filename'],
                    parsed_data.get('content', '')
                )
                
            except Exception as parse_error:
                logger.error(f"Error parsing file {file_id}: {parse_error}")
                continue
        
        return {
            "status": "success",
            "processedFiles": len(document_indexes),
            "documentIndexes": document_indexes
        }
        
    except Exception as e:
        logger.error(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")


def extract_knowledge_entries(file_id: str, filename: str, content: str):
    """
    后台任务：从文档内容中提取知识库条目
    """
    try:
        logger.info(f"Extracting knowledge entries from: {filename}")
        
        # 这里可以调用LLM或规则引擎提取知识点
        # 简化版本：按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        
        # 确保knowledge_base表存在
        try:
            db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    title text NOT NULL,
                    content text NOT NULL,
                    category text DEFAULT 'general',
                    file_id uuid,
                    file_name text,
                    created_at timestamptz DEFAULT now()
                )
            """)
        except:
            pass
        
        # 插入知识条目（示例：提取前10个段落）
        for idx, para in enumerate(paragraphs[:10]):
            try:
                # 生成标题（取前30个字符）
                title = para[:30] + '...' if len(para) > 30 else para
                
                db.execute(
                    """
                    INSERT INTO knowledge_base (title, content, category, file_id, file_name)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (title, para, 'auto-extracted', file_id, filename)
                )
            except Exception as insert_error:
                logger.warning(f"Failed to insert knowledge entry: {insert_error}")
        
        logger.info(f"Knowledge extraction completed for: {filename}")
        
    except Exception as e:
        logger.error(f"Error extracting knowledge entries: {e}")
