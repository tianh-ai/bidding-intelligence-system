#!/usr/bin/env python3
"""检查归档目录中的实际文件"""
import os
from pathlib import Path

archive_base = "/Volumes/ssd/bidding-data/archive"

print("=" * 80)
print("📂 检查归档目录中的实际文件")
print("=" * 80)

if not os.path.exists(archive_base):
    print(f"❌ 归档目录不存在: {archive_base}")
    exit(1)

print(f"\n✅ 归档目录存在: {archive_base}\n")

# 递归遍历所有文件
all_files = []
for root, dirs, files in os.walk(archive_base):
    for file in files:
        if not file.startswith('.'):  # 跳过隐藏文件
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, archive_base)
            size = os.path.getsize(full_path)
            all_files.append({
                'path': rel_path,
                'full_path': full_path,
                'size': size,
                'size_mb': size / 1024 / 1024
            })

if not all_files:
    print("⚠️  归档目录为空，没有文件")
    exit(0)

print(f"📊 找到 {len(all_files)} 个文件\n")
print("=" * 80)

# 按路径排序
all_files.sort(key=lambda x: x['path'])

total_size = 0
for i, file_info in enumerate(all_files, 1):
    print(f"\n{i}. {file_info['path']}")
    print(f"   大小: {file_info['size_mb']:.2f} MB ({file_info['size']:,} bytes)")
    total_size += file_info['size']

print("\n" + "=" * 80)
print(f"📊 统计:")
print(f"   总文件数: {len(all_files)}")
print(f"   总大小: {total_size/1024/1024:.2f} MB ({total_size:,} bytes)")
print("=" * 80)

# 按目录分组统计
from collections import defaultdict
by_dir = defaultdict(list)
for f in all_files:
    dir_name = os.path.dirname(f['path'])
    by_dir[dir_name].append(f)

print("\n📁 按目录分组:")
for dir_name in sorted(by_dir.keys()):
    files_in_dir = by_dir[dir_name]
    dir_size = sum(f['size'] for f in files_in_dir)
    print(f"\n  {dir_name}/ ({len(files_in_dir)} 个文件, {dir_size/1024/1024:.2f} MB)")
    for f in files_in_dir:
        print(f"    - {os.path.basename(f['path'])} ({f['size_mb']:.2f} MB)")

print("\n✅ 检查完成")
