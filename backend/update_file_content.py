#!/usr/bin/env python3
"""
重新解析归档文件并更新数据库content字段
"""
import sys
import os
sys.path.insert(0, '/app')

from database import db
from engines.parse_engine import ParseEngine
from core.logger import logger

parser = ParseEngine()

def update_file_content():
    """重新解析所有归档文件并更新content"""
    
    # 获取所有需要更新的文件
    files = db.query_all("""
        SELECT uf.id, uf.filename, uf.archive_path, f.doc_type
        FROM uploaded_files uf
        JOIN files f ON uf.id = f.id
        WHERE uf.archive_path IS NOT NULL 
        AND f.content IS NULL OR LENGTH(f.content) = 0
        ORDER BY uf.created_at DESC
    """)
    
    logger.info(f"找到 {len(files)} 个需要更新的文件")
    
    updated = 0
    failed = 0
    
    for file in files:
        file_id = file['id']
        archive_path = file['archive_path']
        doc_type = file['doc_type']
        
        if not os.path.exists(archive_path):
            logger.warning(f"文件不存在: {archive_path}")
            failed += 1
            continue
        
        try:
            # 重新解析文件
            result = parser.parse(archive_path, doc_type, save_to_db=False)
            content = result.get('content', '')
            
            if content:
                # 更新数据库
                db.execute(
                    "UPDATE files SET content = %s WHERE id = %s",
                    (content, file_id)
                )
                logger.info(f"✅ 更新成功: {file['filename']} ({len(content)} 字符)")
                updated += 1
            else:
                logger.warning(f"⚠️ 内容为空: {file['filename']}")
                failed += 1
                
        except Exception as e:
            logger.error(f"❌ 处理失败 {file['filename']}: {e}")
            failed += 1
    
    logger.info(f"完成! 成功: {updated}, 失败: {failed}")

if __name__ == '__main__':
    update_file_content()
