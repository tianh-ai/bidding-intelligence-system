#!/usr/bin/env python3
"""
Database Query MCP Server 测试脚本
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from database_query import DatabaseQueryServer, PathMapper


async def test_path_mapper():
    """测试路径转换"""
    print("=== 测试路径转换 ===")
    
    # 容器路径 → 宿主机路径
    container_path = "/app/data/archive/2025/12/proposal/file.docx"
    host_path = PathMapper.to_host_path(container_path)
    print(f"容器路径: {container_path}")
    print(f"宿主机路径: {host_path}")
    assert host_path == "/Volumes/ssd/bidding-data/archive/2025/12/proposal/file.docx"
    
    # 宿主机路径 → 容器路径
    reverse = PathMapper.to_container_path(host_path)
    print(f"转换回: {reverse}")
    assert reverse == container_path
    
    print("✅ 路径转换测试通过\n")


async def test_database_query():
    """测试数据库查询"""
    print("=== 测试数据库查询 ===")
    
    # 设置环境变量
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '5433')
    os.environ.setdefault('DB_NAME', 'bidding_db')
    os.environ.setdefault('DB_USER', 'postgres')
    os.environ.setdefault('DB_PASSWORD', 'postgres123')
    
    server = DatabaseQueryServer()
    
    try:
        # 测试获取统计信息
        print("1. 测试 get_file_stats")
        stats = await server.get_file_stats()
        print(f"   总文件数: {stats['total_files']}")
        print(f"   总大小: {stats['total_size_mb']} MB")
        print(f"   平均大小: {stats['avg_size_mb']} MB")
        print(f"   分类数: {len(stats['by_category'])}")
        print("   ✅ 统计查询成功\n")
        
        # 测试列出最近文件
        print("2. 测试 list_recent_files")
        recent = await server.list_recent_files(limit=5, return_host_path=True)
        print(f"   返回文件数: {recent['total']}")
        if recent['files']:
            first_file = recent['files'][0]
            print(f"   最新文件: {first_file['filename']}")
            print(f"   归档路径: {first_file.get('archive_path', 'N/A')}")
            
            # 验证路径是宿主机格式
            if first_file.get('archive_path'):
                assert first_file['archive_path'].startswith('/Volumes/ssd/'), \
                    "路径应该是宿主机格式"
            print("   ✅ 路径转换为宿主机格式\n")
            
            # 测试查询单个文件
            print("3. 测试 query_file_by_id")
            file_id = first_file['id']
            file_info = await server.query_file_by_id(file_id, return_host_path=True)
            print(f"   文件ID: {file_info['id']}")
            print(f"   文件名: {file_info['filename']}")
            print(f"   分类: {file_info.get('category', 'N/A')}")
            print(f"   大小: {file_info.get('size_mb', 'N/A')} MB")
            print(f"   归档路径: {file_info.get('archive_path', 'N/A')}")
            print("   ✅ 文件查询成功\n")
        
        # 测试搜索功能
        print("4. 测试 search_files")
        search_result = await server.search_files(
            category="proposal",
            limit=3,
            return_host_path=False  # 测试容器路径
        )
        print(f"   搜索结果数: {search_result['total']}")
        if search_result['files']:
            first = search_result['files'][0]
            print(f"   第一个文件: {first['filename']}")
            if first.get('archive_path'):
                assert first['archive_path'].startswith('/app/data/'), \
                    "路径应该是容器格式"
                print(f"   归档路径: {first['archive_path']}")
                print("   ✅ 路径转换为容器格式\n")
        
        print("✅ 所有数据库查询测试通过")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await server.cleanup()


async def main():
    """运行所有测试"""
    print("=== Database Query MCP Server 测试 ===\n")
    
    # 测试1: 路径转换
    await test_path_mapper()
    
    # 测试2: 数据库查询
    try:
        await test_database_query()
    except Exception as e:
        print(f"\n数据库测试需要PostgreSQL运行在 localhost:5433")
        print(f"错误: {e}")
        return 1
    
    print("\n=== 所有测试通过 ✅ ===")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
