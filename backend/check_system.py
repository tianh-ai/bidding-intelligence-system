#!/usr/bin/env python3
"""
系统完整性检查脚本
检查所有模块是否可以正确导入
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("标书智能系统 - 完整性检查")
print("=" * 60)

# 检查列表
checks = []

# 1. 检查database模块
print("\n[1/5] 检查database模块...")
try:
    from database.connection import DatabaseConnection
    print("  ✅ DatabaseConnection 导入成功")
    checks.append(("database.connection", True))
except Exception as e:
    print(f"  ❌ DatabaseConnection 导入失败: {e}")
    checks.append(("database.connection", False))

# 2. 检查engines模块
print("\n[2/5] 检查engines模块...")
try:
    from engines.parse_engine import ParseEngine
    print("  ✅ ParseEngine 导入成功")
    checks.append(("engines.parse_engine", True))
except Exception as e:
    print(f"  ❌ ParseEngine 导入失败: {e}")
    checks.append(("engines.parse_engine", False))

try:
    from engines.chapter_logic_engine import ChapterLogicEngine
    print("  ✅ ChapterLogicEngine 导入成功")
    checks.append(("engines.chapter_logic_engine", True))
except Exception as e:
    print(f"  ❌ ChapterLogicEngine 导入失败: {e}")
    checks.append(("engines.chapter_logic_engine", False))

try:
    from engines.global_logic_engine import GlobalLogicEngine
    print("  ✅ GlobalLogicEngine 导入成功")
    checks.append(("engines.global_logic_engine", True))
except Exception as e:
    print(f"  ❌ GlobalLogicEngine 导入失败: {e}")
    checks.append(("engines.global_logic_engine", False))

# 3. 检查routers模块
print("\n[3/5] 检查routers模块...")
try:
    from routers import files, learning
    print("  ✅ routers.files 导入成功")
    print("  ✅ routers.learning 导入成功")
    checks.append(("routers", True))
except Exception as e:
    print(f"  ❌ routers 导入失败: {e}")
    checks.append(("routers", False))

# 4. 检查main.py
print("\n[4/5] 检查main.py...")
try:
    import main
    print("  ✅ main.py 导入成功")
    checks.append(("main", True))
except Exception as e:
    print(f"  ❌ main.py 导入失败: {e}")
    checks.append(("main", False))

# 5. 检查文件结构
print("\n[5/5] 检查文件结构...")
required_files = [
    "database/__init__.py",
    "database/connection.py",
    "engines/__init__.py",
    "engines/parse_engine.py",
    "engines/chapter_logic_engine.py",
    "engines/global_logic_engine.py",
    "routers/__init__.py",
    "routers/files.py",
    "routers/learning.py",
    "main.py",
    "requirements.txt",
    "init_database.sql",
    ".env.example"
]

all_files_exist = True
for file_path in required_files:
    if os.path.exists(file_path):
        print(f"  ✅ {file_path}")
    else:
        print(f"  ❌ {file_path} 不存在")
        all_files_exist = False

checks.append(("file_structure", all_files_exist))

# 统计结果
print("\n" + "=" * 60)
print("检查结果汇总")
print("=" * 60)

success_count = sum(1 for _, status in checks if status)
total_count = len(checks)

for module, status in checks:
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {module}")

print("\n" + "=" * 60)
print(f"通过: {success_count}/{total_count}")
print("=" * 60)

if success_count == total_count:
    print("\n🎉 所有检查通过!系统完整性验证成功!")
    sys.exit(0)
else:
    print("\n⚠️  部分检查失败,请检查依赖和文件结构")
    sys.exit(1)
