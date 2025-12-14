#!/usr/bin/env python3
"""从数据库查询归档文件路径并验证物理文件是否存在"""
import sys
import os
sys.path.insert(0, '/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend')

from database import db

print("=" * 80)
print("📊 数据库中的归档文件记录 vs 物理文件检查")
print("=" * 80)

# 查询最近上传的文件
files = db.query("""
    SELECT id, filename, semantic_filename, archive_path, category, file_size, created_at
    FROM uploaded_files
    WHERE archive_path IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 30
""")

print(f"\n找到 {len(files)} 条归档记录\n")

exists_count = 0
missing_count = 0
total_size = 0

for i, f in enumerate(files, 1):
    path = f['archive_path']
    exists = os.path.exists(path)
    
    status = "✅" if exists else "❌"
    print(f"\n{i}. {status} {f['filename']}")
    print(f"   语义名: {f['semantic_filename']}")
    print(f"   分类: {f['category']}")
    print(f"   路径: {path}")
    print(f"   大小: {f['file_size']/1024/1024:.2f} MB")
    print(f"   上传: {f['created_at']}")
    
    if exists:
        exists_count += 1
        total_size += f['file_size']
    else:
        missing_count += 1

print("\n" + "=" * 80)
print(f"📊 统计结果:")
print(f"   ✅ 物理文件存在: {exists_count}/{len(files)}")
print(f"   ❌ 物理文件缺失: {missing_count}/{len(files)}")
print(f"   💾 总大小: {total_size/1024/1024:.2f} MB")
print("=" * 80)

# 列出实际存在的文件
if exists_count > 0:
    print(f"\n📁 实际归档目录内容检查:")
    archive_base = "/Volumes/ssd/bidding-data/archive"
    
    if os.path.exists(archive_base):
        # 找到2025目录
        year_dir = os.path.join(archive_base, "2025")
        if os.path.exists(year_dir):
            month_dir = os.path.join(year_dir, "12")
            if os.path.exists(month_dir):
                print(f"\n  {month_dir}/")
                for category in os.listdir(month_dir):
                    cat_path = os.path.join(month_dir, category)
                    if os.path.isdir(cat_path):
                        files_in_cat = [f for f in os.listdir(cat_path) if not f.startswith('.')]
                        print(f"    {category}/ ({len(files_in_cat)} 个文件)")
                        for fname in sorted(files_in_cat):
                            fpath = os.path.join(cat_path, fname)
                            fsize = os.path.getsize(fpath)
                            print(f"      - {fname} ({fsize/1024/1024:.2f} MB)")

print("\n✅ 检查完成")
