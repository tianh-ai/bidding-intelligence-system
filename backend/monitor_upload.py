#!/usr/bin/env python3
"""
实时监控文件上传流程
每3秒检查一次新上传的文件
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import db
from datetime import datetime, timedelta
import time
import os


def check_latest_upload():
    """检查最新上传的文件"""
    
    # 获取最近30秒内的文件
    recent_time = datetime.now() - timedelta(seconds=30)
    
    files = db.query(
        """
        SELECT 
            id, filename, semantic_filename, archive_path, 
            category, status, file_size, created_at
        FROM uploaded_files
        WHERE created_at >= %s
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (recent_time,)
    )
    
    if not files:
        return None
    
    results = []
    for f in files:
        file_id = str(f['id'])
        
        # 检查物理文件
        physical_exists = f['archive_path'] and os.path.exists(f['archive_path'])
        
        # 检查解析内容
        parsed = db.query_one(
            "SELECT LENGTH(content) as content_len FROM files WHERE id = %s",
            (file_id,)
        )
        content_len = parsed['content_len'] if parsed else 0
        
        # 检查章节
        chapters = db.query_one(
            "SELECT COUNT(*) as count FROM chapters WHERE file_id = %s",
            (file_id,)
        )
        chapter_count = chapters['count'] if chapters else 0
        
        # 检查图片
        images = db.query_one(
            "SELECT COUNT(*) as count FROM extracted_images WHERE file_id = %s",
            (file_id,)
        )
        image_count = images['count'] if images else 0
        
        # 检查hash后缀
        has_hash = '_' in (f['semantic_filename'] or '').split('.')[-2][-6:]
        
        results.append({
            'filename': f['filename'],
            'semantic': f['semantic_filename'],
            'has_hash': has_hash,
            'physical_exists': physical_exists,
            'status': f['status'],
            'content_len': content_len,
            'chapters': chapter_count,
            'images': image_count,
            'created_at': f['created_at']
        })
    
    return results


def monitor_uploads(duration_seconds=300):
    """
    持续监控上传
    
    Args:
        duration_seconds: 监控时长（秒），默认5分钟
    """
    
    print("\n" + "="*70)
    print("  📡 实时监控文件上传")
    print(f"  监控时长: {duration_seconds}秒")
    print("="*70 + "\n")
    
    print("等待文件上传...\n")
    
    seen_files = set()
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        results = check_latest_upload()
        
        if results:
            for r in results:
                file_key = (r['filename'], r['created_at'])
                
                if file_key not in seen_files:
                    seen_files.add(file_key)
                    
                    print(f"🆕 {r['filename']}")
                    print(f"   语义名: {r['semantic']}")
                    print(f"   Hash后缀: {'✅' if r['has_hash'] else '❌'}")
                    print(f"   物理文件: {'✅' if r['physical_exists'] else '❌'}")
                    print(f"   状态: {r['status']}")
                    print(f"   解析内容: {r['content_len']} 字符")
                    print(f"   章节数: {r['chapters']}")
                    print(f"   图片数: {r['images']}")
                    
                    # 问题标记
                    issues = []
                    if not r['has_hash']:
                        issues.append("⚠️ 缺少hash后缀")
                    if not r['physical_exists']:
                        issues.append("⚠️ 物理文件不存在")
                    if r['content_len'] < 50 and r['content_len'] > 0:
                        issues.append("⚠️ 内容过短")
                    if r['status'] == 'failed':
                        issues.append("❌ 上传失败")
                    
                    if issues:
                        print(f"   问题: {', '.join(issues)}")
                    else:
                        print(f"   ✅ 正常")
                    
                    print()
        
        time.sleep(3)
    
    print("\n" + "="*70)
    print(f"  监控结束，共发现 {len(seen_files)} 个文件")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        monitor_uploads(duration_seconds=300)  # 监控5分钟
    except KeyboardInterrupt:
        print("\n\n监控中断")
    except Exception as e:
        print(f"\n❌ 监控失败: {e}")
        import traceback
        traceback.print_exc()
