#!/usr/bin/env python3
"""
系统验证脚本 - 验证所有存储位置和数据库配置
"""

import os
import sys
from pathlib import Path

def verify_storage_structure():
    """验证SSD存储结构"""
    print("\n" + "="*60)
    print("🔍 验证SSD存储结构")
    print("="*60)
    
    base_path = "/Volumes/ssd/bidding-data"
    required_dirs = {
        "uploads": "文件上传目录",
        "uploads/temp": "临时文件目录",
        "parsed": "解析结果目录",
        "archive": "归档文件目录",
        "logs": "日志目录",
        "db": "数据库备份目录"
    }
    
    all_ok = True
    for dir_name, description in required_dirs.items():
        full_path = os.path.join(base_path, dir_name)
        exists = os.path.exists(full_path)
        is_dir = os.path.isdir(full_path) if exists else False
        
        if exists and is_dir:
            size = len(os.listdir(full_path)) if dir_name != "db" else 0
            print(f"  ✅ {dir_name:20} - {description}")
        else:
            print(f"  ❌ {dir_name:20} - {description} (缺失)")
            all_ok = False
    
    return all_ok

def verify_config_files():
    """验证配置文件"""
    print("\n" + "="*60)
    print("🔍 验证配置文件")
    print("="*60)
    
    backend_path = "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend"
    
    files_to_check = {
        "core/config.py": "核心配置文件",
        ".env.example": "环境变量示例",
        "routers/files.py": "文件路由配置",
    }
    
    all_ok = True
    for file_name, description in files_to_check.items():
        full_path = os.path.join(backend_path, file_name)
        exists = os.path.exists(full_path)
        
        if exists:
            # 检查是否包含SSD路径
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                has_ssd_path = "/Volumes/ssd/bidding-data" in content
            
            if has_ssd_path:
                print(f"  ✅ {file_name:20} - {description} (已配置SSD)")
            else:
                print(f"  ⚠️  {file_name:20} - {description} (未完全配置)")
                all_ok = False
        else:
            print(f"  ❌ {file_name:20} - {description} (文件缺失)")
            all_ok = False
    
    return all_ok

def verify_permissions():
    """验证目录权限"""
    print("\n" + "="*60)
    print("🔍 验证目录权限")
    print("="*60)
    
    base_path = "/Volumes/ssd/bidding-data"
    
    # 检查基础目录权限
    if os.path.exists(base_path):
        # 检查读写权限
        can_read = os.access(base_path, os.R_OK)
        can_write = os.access(base_path, os.W_OK)
        
        if can_read and can_write:
            print(f"  ✅ /Volumes/ssd/bidding-data - 读写权限正常")
            return True
        else:
            print(f"  ❌ /Volumes/ssd/bidding-data - 权限不足")
            print(f"     可读: {can_read}, 可写: {can_write}")
            return False
    else:
        print(f"  ❌ /Volumes/ssd/bidding-data - 目录不存在")
        return False

def verify_python_packages():
    """验证Python包"""
    print("\n" + "="*60)
    print("🔍 验证Python包")
    print("="*60)
    
    required_packages = [
        ("fastapi", "FastAPI框架"),
        ("pydantic", "数据验证"),
        ("psycopg2", "PostgreSQL驱动"),
        ("sqlalchemy", "ORM框架"),
        ("asyncio", "异步编程"),
    ]
    
    all_ok = True
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package:20} - {description}")
        except ImportError:
            print(f"  ❌ {package:20} - {description} (未安装)")
            all_ok = False
    
    return all_ok

def check_database_connection():
    """检查数据库连接配置"""
    print("\n" + "="*60)
    print("🔍 检查数据库配置")
    print("="*60)
    
    try:
        # 添加后端到路径
        sys.path.insert(0, '/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend')
        from core.config import get_settings
        
        settings = get_settings()
        print(f"  ✅ 数据库主机: {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"  ✅ 数据库名称: {settings.DB_NAME}")
        print(f"  ✅ 用户名: {settings.DB_USER}")
        print(f"  ✅ 上传目录: {settings.UPLOAD_DIR}")
        print(f"  ✅ 日志目录: {settings.LOG_DIR}")
        return True
    except Exception as e:
        print(f"  ❌ 无法加载配置: {e}")
        return False

def main():
    """主验证函数"""
    print("\n" + "🚀"*20)
    print("投标智能系统 - 完整验证")
    print("🚀"*20)
    
    results = {
        "存储结构": verify_storage_structure(),
        "配置文件": verify_config_files(),
        "目录权限": verify_permissions(),
        "Python包": verify_python_packages(),
        "数据库配置": check_database_connection(),
    }
    
    print("\n" + "="*60)
    print("📊 验证结果总结")
    print("="*60)
    
    all_passed = all(results.values())
    
    for check_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {check_name:15} {status}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有验证通过！系统已就绪")
        print("\n下一步:")
        print("  1. 启动PostgreSQL数据库")
        print("  2. 运行: python3 init_database.py")
        print("  3. 运行: python3 main.py")
    else:
        print("❌ 部分验证失败，请检查上述问题")
    
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
