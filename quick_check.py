#!/usr/bin/env python3
import os

# 直接检查目录
archive = "/Volumes/ssd/bidding-data/archive"
print(f"检查: {archive}")
print(f"存在: {os.path.exists(archive)}")

if os.path.exists(archive):
    items = os.listdir(archive)
    print(f"内容: {items}")
    
    # 检查2025目录
    y2025 = os.path.join(archive, "2025")
    if os.path.exists(y2025):
        print(f"\n2025/ 存在")
        m12 = os.path.join(y2025, "12")
        if os.path.exists(m12):
            print(f"2025/12/ 存在")
            cats = os.listdir(m12)
            print(f"分类: {cats}")
            
            for cat in cats:
                cat_path = os.path.join(m12, cat)
                if os.path.isdir(cat_path):
                    files = [f for f in os.listdir(cat_path) if not f.startswith('.')]
                    print(f"\n{cat}/ 有 {len(files)} 个文件:")
                    for f in files[:5]:  # 只显示前5个
                        print(f"  - {f}")
                    if len(files) > 5:
                        print(f"  ... 还有 {len(files)-5} 个文件")
