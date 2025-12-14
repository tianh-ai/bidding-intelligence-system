#!/usr/bin/env python3
"""立即执行：复制所有文件到 SSD"""
import os
import shutil
import subprocess

print("🔧 开始复制文件到 SSD...\n")

ssd_base = "/Volumes/ssd/bidding-data"
backend_base = "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend"

# 1. 创建目录
os.makedirs(f"{ssd_base}/uploads/temp", exist_ok=True)
os.makedirs(f"{ssd_base}/archive", exist_ok=True)
os.makedirs(f"{ssd_base}/images", exist_ok=True)
os.makedirs(f"{ssd_base}/logs", exist_ok=True)
print("✓ SSD 目录已创建")

# 2. 从容器复制（如果容器在运行）
print("\n📦 从容器复制文件...")
try:
    subprocess.run(['docker', 'start', 'bidding_backend'], check=False, capture_output=True)
    result = subprocess.run(
        ['docker', 'cp', 'bidding_backend:/Volumes/ssd/bidding-data/', '/Volumes/ssd/'],
        capture_output=True, text=True, timeout=30
    )
    subprocess.run(['docker', 'stop', 'bidding_backend'], check=False, capture_output=True)
    print("✓ 容器文件已复制" if result.returncode == 0 else f"⚠ {result.stderr[:100]}")
except Exception as e:
    print(f"⚠ 容器操作失败: {e}")

# 3. 从项目目录复制
print("\n📦 从项目复制文件...")
src_archive = f"{backend_base}/uploads/archive"
dst_archive = f"{ssd_base}/archive"

if os.path.exists(src_archive):
    for root, dirs, files in os.walk(src_archive):
        for f in files:
            src_file = os.path.join(root, f)
            rel = os.path.relpath(src_file, src_archive)
            dst_file = os.path.join(dst_archive, rel)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            print(f"  ✓ {rel}")

# 4. 验证
print("\n📊 验证 SSD 文件:")
files = []
for root, dirs, filenames in os.walk(dst_archive):
    for f in filenames:
        if f.endswith(('.docx', '.pdf')):
            full = os.path.join(root, f)
            files.append(os.path.relpath(full, ssd_base))

for i, f in enumerate(files[:15], 1):
    print(f"  {i}. {f}")

print(f"\n✅ 总共 {len(files)} 个文件在 SSD 上")
print(f"📁 路径: {dst_archive}")
