#!/usr/bin/env python3
"""
完整上传流程检查脚本
验证: 文件存储、数据库记录、图片提取、章节解析的完整性
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import db
from datetime import datetime, timedelta
import os


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_recent_uploads():
    """检查最近上传的文件"""
    print_header("1. 检查最近上传的文件 (数据库记录)")
    
    # 获取最近2小时内上传的文件
    recent_time = datetime.now() - timedelta(hours=2)
    
    files = db.query(
        """
        SELECT 
            id, filename, semantic_filename,
            archive_path, category, status, file_size,
            created_at, status_updated_at
        FROM uploaded_files
        WHERE created_at >= %s
        ORDER BY created_at DESC
        """,
        (recent_time,)
    )
    
    if not files:
        print("⚠️  最近2小时内没有上传文件")
        print("提示: 请先上传文件后再运行此检查")
        return []
    
    print(f"找到 {len(files)} 个最近上传的文件:\n")
    
    for i, f in enumerate(files, 1):
        print(f"文件 {i}:")
        print(f"  ID: {f['id']}")
        print(f"  文件名: {f['filename']}")
        print(f"  语义文件名: {f['semantic_filename']}")
        print(f"  分类: {f['category']}")
        print(f"  状态: {f['status']}")
        print(f"  文件大小: {f['file_size']} bytes")
        print(f"  归档路径: {f['archive_path']}")
        print(f"  上传时间: {f['created_at']}")
        print()
    
    return files


def check_physical_files(files):
    """检查物理文件是否存在"""
    print_header("2. 检查物理文件存储")
    
    all_exist = True
    
    for f in files:
        archive_path = f['archive_path']
        filename = f['semantic_filename'] or f['filename']
        
        print(f"文件: {filename}")
        print(f"  路径: {archive_path}")
        
        if not archive_path:
            print(f"  ❌ archive_path 为空")
            all_exist = False
        elif os.path.exists(archive_path):
            size = os.path.getsize(archive_path)
            print(f"  ✅ 文件存在 ({size} bytes)")
            
            # 检查大小是否匹配
            if f['file_size'] and abs(size - f['file_size']) > 1000:
                print(f"  ⚠️  大小不匹配 (数据库:{f['file_size']}, 实际:{size})")
        else:
            print(f"  ❌ 文件不存在")
            all_exist = False
        print()
    
    if all_exist:
        print("✅ 所有文件物理存储正确")
    else:
        print("❌ 部分文件物理存储缺失")
    
    return all_exist


def check_parsed_content(files):
    """检查解析内容"""
    print_header("3. 检查文件解析内容 (files表)")
    
    all_parsed = True
    
    for f in files:
        file_id = str(f['id'])
        filename = f['semantic_filename'] or f['filename']
        
        print(f"文件: {filename}")
        
        # 查询files表
        parsed = db.query_one(
            "SELECT id, filename, content, doc_type, created_at FROM files WHERE id = %s",
            (file_id,)
        )
        
        if not parsed:
            print(f"  ❌ files表中没有记录")
            all_parsed = False
        else:
            content_len = len(parsed['content'] or '')
            print(f"  ✅ 已解析")
            print(f"  文档类型: {parsed['doc_type']}")
            print(f"  内容长度: {content_len} 字符")
            
            if content_len == 0:
                print(f"  ⚠️  内容为空，可能解析失败")
                all_parsed = False
            elif content_len < 50:
                print(f"  ⚠️  内容过短，可能解析不完整")
        print()
    
    if all_parsed:
        print("✅ 所有文件已正确解析")
    else:
        print("❌ 部分文件解析异常")
    
    return all_parsed


def check_chapters(files):
    """检查章节提取"""
    print_header("4. 检查章节结构提取 (chapters表)")
    
    all_have_chapters = True
    
    for f in files:
        file_id = str(f['id'])
        filename = f['semantic_filename'] or f['filename']
        
        print(f"文件: {filename}")
        
        # 查询章节
        chapters = db.query(
            """
            SELECT 
                id, chapter_number, chapter_title, chapter_level,
                LENGTH(content) as content_len, position_order
            FROM chapters
            WHERE file_id = %s
            ORDER BY position_order
            """,
            (file_id,)
        )
        
        if not chapters:
            print(f"  ⚠️  没有章节记录（可能是单章节文档）")
        else:
            print(f"  ✅ 提取了 {len(chapters)} 个章节:")
            
            for ch in chapters[:5]:  # 只显示前5个
                print(f"    {ch['chapter_number']}. {ch['chapter_title'][:40]}")
                print(f"       级别:{ch['chapter_level']}, 内容:{ch['content_len']}字符")
            
            if len(chapters) > 5:
                print(f"    ... 还有 {len(chapters) - 5} 个章节")
        print()
    
    return all_have_chapters


def check_images(files):
    """检查图片提取"""
    print_header("5. 检查图片提取 (extracted_images表)")
    
    total_images = 0
    
    for f in files:
        file_id = str(f['id'])
        filename = f['semantic_filename'] or f['filename']
        
        print(f"文件: {filename}")
        
        # 查询图片
        images = db.query(
            """
            SELECT 
                id, image_path, image_number, format, 
                size, width, height, hash
            FROM extracted_images
            WHERE file_id = %s
            ORDER BY image_number
            """,
            (file_id,)
        )
        
        if not images:
            print(f"  ℹ️  没有提取到图片（文档可能不包含图片）")
        else:
            print(f"  ✅ 提取了 {len(images)} 张图片:")
            total_images += len(images)
            
            for img in images[:3]:  # 只显示前3张
                print(f"    图片 {img['image_number']}: {img['format']}, {img['width']}x{img['height']}, {img['size']} bytes")
                print(f"      路径: {img['image_path']}")
                
                # 检查图片文件是否存在
                if os.path.exists(img['image_path']):
                    print(f"      ✅ 文件存在")
                else:
                    print(f"      ❌ 文件不存在")
            
            if len(images) > 3:
                print(f"    ... 还有 {len(images) - 3} 张图片")
        print()
    
    print(f"总计提取图片: {total_images} 张")
    return total_images


def check_storage_structure():
    """检查存储目录结构"""
    print_header("6. 检查存储目录结构")
    
    base_path = Path("/Volumes/ssd/bidding-data")
    
    directories = {
        "临时上传": base_path / "uploads" / "temp",
        "归档目录": base_path / "archive",
        "图片目录": base_path / "images",
        "日志目录": base_path / "logs",
    }
    
    for name, path in directories.items():
        print(f"{name}: {path}")
        if path.exists():
            # 统计文件数量
            if path.is_dir():
                file_count = sum(1 for _ in path.rglob('*') if _.is_file())
                dir_count = sum(1 for _ in path.rglob('*') if _.is_dir())
                print(f"  ✅ 存在 ({file_count} 个文件, {dir_count} 个子目录)")
            else:
                print(f"  ✅ 存在")
        else:
            print(f"  ❌ 不存在")
        print()


def check_knowledge_base():
    """检查知识库向量化"""
    print_header("7. 检查知识库向量化 (可选)")
    
    # 检查是否有向量表
    try:
        tables = db.query(
            """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename LIKE '%vector%' OR tablename LIKE '%embedding%'
            """
        )
        
        if tables:
            print("找到向量相关表:")
            for t in tables:
                print(f"  - {t['tablename']}")
                
                # 统计记录数
                count = db.query_one(f"SELECT COUNT(*) as count FROM {t['tablename']}")
                print(f"    记录数: {count['count']}")
        else:
            print("ℹ️  未发现向量表（知识库功能可能未启用）")
            
    except Exception as e:
        print(f"⚠️  检查向量表失败: {e}")


def generate_report(files):
    """生成检查报告"""
    print_header("检查总结")
    
    print(f"📊 上传文件数: {len(files)}")
    
    # 统计各项指标
    total_size = sum(f['file_size'] or 0 for f in files)
    
    total_parsed = db.query_one(
        """
        SELECT COUNT(*) as count, SUM(LENGTH(content)) as total_content
        FROM files
        WHERE id = ANY(%s::uuid[])
        """,
        ([str(f['id']) for f in files],)
    )
    
    total_chapters = db.query_one(
        """
        SELECT COUNT(*) as count
        FROM chapters
        WHERE file_id = ANY(%s::uuid[])
        """,
        ([str(f['id']) for f in files],)
    )
    
    total_images = db.query_one(
        """
        SELECT COUNT(*) as count, SUM(size) as total_size
        FROM extracted_images
        WHERE file_id = ANY(%s::uuid[])
        """,
        ([str(f['id']) for f in files],)
    )
    
    print(f"📁 文件总大小: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"📄 解析内容总长度: {total_parsed['total_content'] or 0:,} 字符")
    print(f"📑 章节总数: {total_chapters['count'] or 0}")
    print(f"🖼️  图片总数: {total_images['count'] or 0} 张 ({(total_images['total_size'] or 0)/1024:.1f} KB)")
    
    print("\n" + "="*70)


def main():
    """主函数"""
    print("\n" + "="*70)
    print("  标书智能系统 - 上传流程完整性检查")
    print("  检查范围: 最近2小时内上传的文件")
    print("="*70)
    
    try:
        # 1. 检查数据库记录
        files = check_recent_uploads()
        
        if not files:
            return
        
        # 2. 检查物理文件
        check_physical_files(files)
        
        # 3. 检查解析内容
        check_parsed_content(files)
        
        # 4. 检查章节
        check_chapters(files)
        
        # 5. 检查图片
        check_images(files)
        
        # 6. 检查存储结构
        check_storage_structure()
        
        # 7. 检查知识库
        check_knowledge_base()
        
        # 8. 生成报告
        generate_report(files)
        
        print("\n✅ 检查完成!")
        
    except KeyboardInterrupt:
        print("\n\n检查中断")
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
