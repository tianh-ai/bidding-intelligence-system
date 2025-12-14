#!/usr/bin/env python3
"""
修复卡在 parsing 状态的文件
手动触发解析并更新数据库
"""
import sys
import os

# 修复导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, '..'))

from database import db
from engines.parse_engine import ParseEngine
from engines.document_classifier import DocumentClassifier
from core.logger import logger
import json
from datetime import datetime
import shutil

# 初始化
parse_engine = ParseEngine()
classifier = DocumentClassifier()

# 目录配置
ARCHIVE_DIR = "./uploads/archive"
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def fix_stuck_file(file_id: str):
    """修复单个卡住的文件"""
    try:
        # 1. 从数据库获取文件信息
        file_info = db.query_one(
            "SELECT * FROM uploaded_files WHERE id = %s",
            (file_id,)
        )
        
        if not file_info:
            logger.error(f"文件不存在: {file_id}")
            return False
        
        filename = file_info['filename']
        temp_path = file_info['temp_path']
        
        logger.info(f"📄 处理文件: {filename}")
        logger.info(f"   路径: {temp_path}")
        
        # 2. 检查文件是否存在
        if not os.path.exists(temp_path):
            logger.error(f"文件不存在于磁盘: {temp_path}")
            db.execute(
                "UPDATE uploaded_files SET status = 'failed' WHERE id = %s",
                (file_id,)
            )
            return False
        
        # 3. 解析文件（使用底层方法避免重复保存DB）
        logger.info("🔄 开始解析...")
        db.execute(
            "UPDATE uploaded_files SET status = 'parsing' WHERE id = %s",
            (file_id,)
        )
        
        # 调用底层解析方法（不保存DB）
        if temp_path.endswith('.pdf'):
            content = parse_engine._parse_pdf(temp_path)
        else:
            logger.error(f"暂不支持的文件类型: {temp_path}")
            return False
        
        chapters = parse_engine._extract_from_content(content)
        
        logger.info(f"✅ 解析完成: {len(chapters)} 个章节")
        
        # 4. 生成元数据
        metadata = {
            "chapters": [
                {
                    "title": ch.get('chapter_title', ''),
                    "level": ch.get('chapter_level', 1),
                    "page": ch.get('page', 0),
                    "number": ch.get('chapter_number', '')
                }
                for ch in chapters
            ],
            "page_count": len(chapters),
            "has_tables": False,  # 简化：不检测表格
            "parse_time": datetime.now().isoformat()
        }
        
        # 5. 智能分类
        category, semantic_filename = classifier.classify(
            filename,
            metadata,
            content
        )
        
        logger.info(f"🏷️  分类: {category}, 语义名: {semantic_filename}")
        
        # 6. 归档文件
        now = datetime.now()
        year = now.year
        month = now.month
        archive_dir = os.path.join(ARCHIVE_DIR, str(year), f"{month:02d}", category)
        os.makedirs(archive_dir, exist_ok=True)
        
        archive_path = os.path.join(archive_dir, semantic_filename)
        shutil.copy2(temp_path, archive_path)
        
        logger.info(f"📦 归档到: {archive_path}")
        
        # 7. 更新数据库
        db.execute(
            """
            UPDATE uploaded_files 
            SET status = 'archived', 
                archive_path = %s, 
                category = %s, 
                semantic_filename = %s,
                metadata = %s,
                parsed_at = NOW(),
                archived_at = NOW(),
                file_path = %s
            WHERE id = %s
            """,
            (archive_path, category, semantic_filename, json.dumps(metadata), archive_path, file_id)
        )
        
        # 8. 插入到 files 表（使用 reference 类型，添加 filetype）
        file_ext = os.path.splitext(filename)[1][1:]  # 去掉点号
        db.execute(
            """
            INSERT INTO files (id, filename, filepath, filetype, doc_type, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 'reference', NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET
                filename = EXCLUDED.filename,
                filepath = EXCLUDED.filepath,
                filetype = EXCLUDED.filetype,
                updated_at = NOW()
            """,
            (file_id, semantic_filename, archive_path, file_ext)
        )
        
        # 9. 插入章节
        for idx, ch in enumerate(chapters):
            db.execute(
                """
                INSERT INTO chapters (
                    file_id, chapter_title, chapter_level, content, 
                    chapter_number, position_order, structure_data
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    file_id,
                    ch.get('chapter_title', ''),
                    ch.get('chapter_level', 1),
                    ch.get('content', ''),
                    ch.get('chapter_number', ''),
                    idx + 1,  # position_order 从1开始
                    json.dumps({"page": ch.get('page', 0)})
                )
            )
        
        logger.info(f"✅ 完成！章节已插入: {len(chapters)} 条")
        return True
        
    except Exception as e:
        import traceback
        error_msg = f"处理失败: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        db.execute(
            "UPDATE uploaded_files SET status = 'failed' WHERE id = %s",
            (file_id,)
        )
        return False

if __name__ == "__main__":
    # 查找所有卡在 parsing 状态的文件
    stuck_files = db.query(
        """
        SELECT id, filename, created_at 
        FROM uploaded_files 
        WHERE status = 'parsing' 
        AND parsed_at IS NULL
        ORDER BY created_at DESC
        """
    )
    
    if not stuck_files:
        logger.info("没有卡住的文件")
        sys.exit(0)
    
    logger.info(f"找到 {len(stuck_files)} 个卡住的文件")
    
    success_count = 0
    for file in stuck_files:
        logger.info(f"\n{'='*60}")
        if fix_stuck_file(file['id']):
            success_count += 1
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ 成功: {success_count}/{len(stuck_files)}")
