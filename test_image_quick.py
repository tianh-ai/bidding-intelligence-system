#!/usr/bin/env python3
"""
简化的图片提取测试 - 直接在第一个DOCX文件上测试
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from engines.image_extractor import ImageExtractor
from database import db
from core.logger import logger


def main():
    print("\n=== 图片提取功能快速测试 ===\n")
    
    # 1. 获取第一个DOCX文件
    print("1. 查询数据库中的DOCX文件...")
    files = db.query(
        "SELECT id, filename, archive_path, created_at FROM uploaded_files WHERE filename LIKE %s LIMIT 1",
        ('%.docx',)
    )
    
    if not files:
        print("   ❌ 没有找到DOCX文件,请先上传")
        return
    
    file_info = files[0]
    print(f"   找到文件: {file_info['filename']}")
    print(f"   路径: {file_info['archive_path']}")
    
    # 2. 提取图片
    print("\n2. 提取图片...")
    extractor = ImageExtractor()
    
    try:
        images = extractor.extract_from_docx(
            docx_path=file_info['archive_path'],
            file_id=str(file_info['id']),
            year=file_info['created_at'].year
        )
        
        print(f"   ✅ 成功提取 {len(images)} 张图片\n")
        
        # 3. 显示结果
        if images:
            for img in images[:3]:
                print(f"   图片 {img['image_number']}:")
                print(f"     格式: {img['format']}, 大小: {img['width']}x{img['height']}, {img['size']} bytes")
                print(f"     路径: {img['image_path']}")
            
            if len(images) > 3:
                print(f"   ... 还有 {len(images) - 3} 张")
        
        # 4. 验证数据库
        print(f"\n3. 验证数据库记录...")
        db_count = db.query_one(
            "SELECT COUNT(*) as count FROM extracted_images WHERE file_id = %s",
            (str(file_info['id']),)
        )
        print(f"   数据库中有 {db_count['count']} 条记录")
        
        if db_count['count'] == len(images):
            print("   ✅ 数量匹配")
        else:
            print(f"   ⚠️  数量不匹配")
            
    except Exception as e:
        print(f"   ❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
