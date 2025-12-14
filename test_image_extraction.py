#!/usr/bin/env python3
"""
测试图片提取功能
验证从DOCX/PDF文档提取图片并保存到磁盘的完整流程
"""

import sys
import os
from pathlib import Path

# 添加backend到Python路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from engines.image_extractor import ImageExtractor
from database import db
from core.logger import logger
import uuid


def test_image_extraction():
    """测试图片提取功能"""
    
    print("\n" + "="*60)
    print("图片提取功能测试")
    print("="*60 + "\n")
    
    # 1. 初始化ImageExtractor
    print("1. 初始化 ImageExtractor...")
    extractor = ImageExtractor()
    print(f"   ✅ 存储目录: {extractor.storage_base}\n")
    
    # 2. 查找测试文件
    print("2. 查找包含图片的测试文件...")
    test_files = []
    
    # 从数据库查找已上传的DOCX文件
    try:
        uploaded_files = db.query(
            """
            SELECT id, filename, archive_path, created_at
            FROM uploaded_files
            WHERE filename LIKE '%.docx'
            AND archive_path IS NOT NULL
            LIMIT 5
            """
        )
        
        if uploaded_files:
            print(f"   找到 {len(uploaded_files)} 个DOCX文件:")
            for f in uploaded_files:
                print(f"     - {f['filename']}")
                test_files.append(f)
        else:
            print("   ⚠️  数据库中没有找到DOCX文件")
            
    except Exception as e:
        print(f"   ❌ 查询数据库失败: {e}")
        return
    
    if not test_files:
        print("\n   提示: 请先上传包含图片的DOCX文件")
        return
    
    # 3. 测试提取第一个文件的图片
    print("\n3. 测试提取图片...")
    test_file = test_files[0]
    file_path = test_file['archive_path']
    file_id = str(test_file['id'])
    year = test_file['created_at'].year
    
    print(f"   文件: {test_file['filename']}")
    print(f"   路径: {file_path}")
    print(f"   年份: {year}")
    
    if not os.path.exists(file_path):
        print(f"   ❌ 文件不存在: {file_path}")
        return
    
    try:
        # 提取图片
        print(f"\n   正在提取图片...")
        images = extractor.extract_from_docx(file_path, file_id, year)
        
        print(f"   ✅ 成功提取 {len(images)} 张图片\n")
        
        if images:
            print("   提取的图片信息:")
            for i, img in enumerate(images[:5], 1):  # 只显示前5张
                print(f"\n   图片 {i}:")
                print(f"     - 编号: {img['image_number']}")
                print(f"     - 格式: {img['format']}")
                print(f"     - 尺寸: {img['width']}x{img['height']}")
                print(f"     - 大小: {img['size']} bytes")
                print(f"     - 路径: {img['image_path']}")
                print(f"     - Hash: {img['hash']}")
                
                # 验证文件是否存在
                if os.path.exists(img['image_path']):
                    print(f"     ✅ 文件已保存")
                else:
                    print(f"     ❌ 文件不存在")
            
            if len(images) > 5:
                print(f"\n   ... 还有 {len(images) - 5} 张图片")
        
    except Exception as e:
        print(f"   ❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 验证数据库记录
    print("\n4. 验证数据库记录...")
    try:
        db_images = db.query(
            "SELECT id, image_number, format, size FROM extracted_images WHERE file_id = %s ORDER BY image_number",
            (file_id,)
        )
        
        print(f"   数据库中有 {len(db_images)} 条记录")
        
        if len(db_images) != len(images):
            print(f"   ⚠️  数量不匹配: 提取了{len(images)}张, 数据库{len(db_images)}条")
        else:
            print(f"   ✅ 数量匹配")
            
    except Exception as e:
        print(f"   ❌ 查询数据库失败: {e}")
    
    # 5. 测试API查询
    print("\n5. 测试ImageExtractor查询方法...")
    try:
        # 通过file_id查询
        file_images = extractor.get_file_images(file_id)
        print(f"   get_file_images(): {len(file_images)} 张图片")
        
        # 通过年份查询
        year_images = extractor.get_images_by_year(year)
        print(f"   get_images_by_year({year}): {len(year_images)} 张图片")
        
        print(f"   ✅ 查询方法正常工作")
        
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
    
    # 6. 检查存储目录
    print("\n6. 检查存储目录结构...")
    year_dir = extractor.storage_base / str(year)
    if year_dir.exists():
        print(f"   ✅ 年份目录存在: {year_dir}")
        
        file_dir = year_dir / file_id
        if file_dir.exists():
            print(f"   ✅ 文件目录存在: {file_dir}")
            
            # 统计实际文件
            actual_files = list(file_dir.glob("*"))
            print(f"   实际文件数: {len(actual_files)}")
            
            if actual_files:
                print(f"\n   示例文件:")
                for f in actual_files[:3]:
                    print(f"     - {f.name} ({f.stat().st_size} bytes)")
        else:
            print(f"   ❌ 文件目录不存在")
    else:
        print(f"   ❌ 年份目录不存在")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        test_image_extraction()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
