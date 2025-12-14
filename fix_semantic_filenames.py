#!/usr/bin/env python3
"""
紧急修复脚本：修正已上传文件的语义文件名
为所有没有hash后缀的文件重新生成唯一文件名
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import db
from engines.document_classifier import DocumentClassifier
import shutil
import os


def fix_uploaded_files():
    """修复所有没有hash后缀的文件"""
    
    print("\n" + "="*70)
    print("  紧急修复：为已上传文件添加hash后缀")
    print("="*70 + "\n")
    
    # 获取所有语义文件名没有hash的文件
    files = db.query(
        """
        SELECT id, filename, semantic_filename, archive_path, category
        FROM uploaded_files
        WHERE semantic_filename IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 100
        """
    )
    
    if not files:
        print("✅ 没有需要修复的文件")
        return
    
    print(f"找到 {len(files)} 个需要修复的文件\n")
    
    classifier = DocumentClassifier()
    fixed_count = 0
    failed_count = 0
    
    for f in files:
        file_id = str(f['id'])
        old_semantic = f['semantic_filename']
        old_path = f['archive_path']
        original_filename = f['filename']
        category = f['category']
        
        print(f"处理: {original_filename}")
        print(f"  当前语义名: {old_semantic}")
        
        try:
            # 生成新的语义文件名（带hash）
            new_semantic = classifier.generate_semantic_filename(
                original_filename=original_filename,
                category=category,
                metadata={},
                content=''
            )
            
            print(f"  新语义名: {new_semantic}")
            
            if old_semantic == new_semantic:
                print(f"  ℹ️  文件名未变化，跳过")
                continue
            
            # 生成新路径
            new_path = old_path.replace(old_semantic, new_semantic) if old_path else None
            
            if new_path and old_path and os.path.exists(old_path):
                # 确保新路径的目录存在
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                
                # 如果新文件已存在，添加额外后缀
                if os.path.exists(new_path):
                    print(f"  ⚠️  目标文件已存在: {new_path}")
                    # 不覆盖，保留旧的
                    print(f"  ℹ️  只更新数据库记录")
                else:
                    # 移动文件
                    shutil.move(old_path, new_path)
                    print(f"  ✅ 文件已移动到: {new_path}")
            else:
                if not old_path:
                    print(f"  ⚠️  archive_path为空")
                elif not os.path.exists(old_path):
                    print(f"  ⚠️  原文件不存在: {old_path}")
                new_path = None
            
            # 更新数据库
            db.execute(
                """
                UPDATE uploaded_files
                SET semantic_filename = %s,
                    archive_path = %s
                WHERE id = %s
                """,
                (new_semantic, new_path or old_path, file_id)
            )
            
            print(f"  ✅ 数据库已更新")
            fixed_count += 1
            
        except Exception as e:
            print(f"  ❌ 修复失败: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
        
        print()
    
    print("="*70)
    print(f"修复完成: 成功{fixed_count}个, 失败{failed_count}个")
    print("="*70 + "\n")
    
    # 显示当前文件分布
    print("\n当前归档目录文件分布:")
    print()
    
    archive_base = Path("/Volumes/ssd/bidding-data/archive")
    if archive_base.exists():
        for category_dir in ['tender', 'proposal', 'reference']:
            category_path = archive_base / "2025" / "12" / category_dir
            if category_path.exists():
                files = list(category_path.glob("*.docx"))
                print(f"  {category_dir}/: {len(files)} 个文件")
                for f in files[:5]:
                    size_mb = f.stat().st_size / 1024 / 1024
                    print(f"    - {f.name} ({size_mb:.2f} MB)")
                if len(files) > 5:
                    print(f"    ... 还有 {len(files)-5} 个")
            else:
                print(f"  {category_dir}/: 目录不存在")
            print()


def check_duplicates():
    """检查是否还有重复的语义文件名"""
    print("\n检查重复文件名...")
    
    duplicates = db.query(
        """
        SELECT semantic_filename, COUNT(*) as count
        FROM uploaded_files
        WHERE semantic_filename IS NOT NULL
        GROUP BY semantic_filename
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        """
    )
    
    if duplicates:
        print(f"\n⚠️  发现 {len(duplicates)} 组重复文件名:")
        for dup in duplicates:
            print(f"  - {dup['semantic_filename']}: {dup['count']} 个文件")
    else:
        print("✅ 没有重复文件名")


if __name__ == "__main__":
    try:
        fix_uploaded_files()
        check_duplicates()
        
        print("\n💡 建议:")
        print("1. 重新上传之前丢失的文件（如果还有备份）")
        print("2. 清理数据库中的重复记录")
        print("3. 验证所有文件的物理存储和解析内容")
        
    except KeyboardInterrupt:
        print("\n\n修复中断")
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
