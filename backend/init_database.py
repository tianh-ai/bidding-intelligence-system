#!/usr/bin/env python3
"""
数据库初始化脚本 - 创建所有必需的表和初始数据
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加后端目录到Python路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from core.config import get_settings
from core.logger import logger
from db.ontology import OntologyDB

async def init_database():
    """初始化数据库"""
    try:
        settings = get_settings()
        logger.info(f"连接数据库: {settings.database_url}")
        
        db = OntologyDB()
        await db.init()
        
        logger.info("✅ 数据库初始化完成")
        
        # 创建知识库表
        await create_knowledge_base_table(db)
        
        # 创建上传文件表
        await create_uploaded_files_table(db)
        
        # 创建解析结果表
        await create_parsing_results_table(db)
        
        logger.info("✅ 所有表创建完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False

async def create_knowledge_base_table(db):
    """创建知识库表"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            file_id UUID,
            file_name TEXT,
            source TEXT DEFAULT 'manual',
            embedding VECTOR(1536),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ knowledge_base 表已创建")
        
        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_base_file_id 
            ON knowledge_base(file_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_base_category 
            ON knowledge_base(category)
        """)
        
    except Exception as e:
        logger.warning(f"knowledge_base 表可能已存在: {e}")

async def create_uploaded_files_table(db):
    """创建上传文件表"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            file_type TEXT,
            mime_type TEXT,
            upload_status TEXT DEFAULT 'pending',
            parse_status TEXT DEFAULT 'pending',
            storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ uploaded_files 表已创建")
        
        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_uploaded_files_name 
            ON uploaded_files(file_name)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_uploaded_files_status 
            ON uploaded_files(upload_status, parse_status)
        """)
        
    except Exception as e:
        logger.warning(f"uploaded_files 表可能已存在: {e}")

async def create_parsing_results_table(db):
    """创建解析结果表"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS parsing_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
            chapter_count INTEGER,
            parsing_time FLOAT,
            parsing_status TEXT DEFAULT 'pending',
            error_message TEXT,
            result_json JSONB,
            storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data/parsed',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ parsing_results 表已创建")
        
        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_parsing_results_file_id 
            ON parsing_results(file_id)
        """)
        
    except Exception as e:
        logger.warning(f"parsing_results 表可能已存在: {e}")

async def verify_storage_paths():
    """验证存储路径"""
    paths = [
        "/Volumes/ssd/bidding-data/uploads",
        "/Volumes/ssd/bidding-data/parsed",
        "/Volumes/ssd/bidding-data/archive",
        "/Volumes/ssd/bidding-data/logs"
    ]
    
    logger.info("验证存储路径:")
    for path in paths:
        if os.path.exists(path):
            logger.info(f"  ✓ {path}")
        else:
            logger.warning(f"  ⚠️  {path} 不存在，正在创建...")
            os.makedirs(path, exist_ok=True)

async def main():
    """主函数"""
    print("="*60)
    print("🚀 数据库初始化")
    print("="*60)
    print()
    
    # 验证存储路径
    await verify_storage_paths()
    print()
    
    # 初始化数据库
    success = await init_database()
    
    print()
    print("="*60)
    if success:
        print("✅ 数据库初始化完成！")
        print()
        print("存储配置:")
        print("  - 文件上传: /Volumes/ssd/bidding-data/uploads")
        print("  - 解析结果: /Volumes/ssd/bidding-data/parsed")
        print("  - 归档文件: /Volumes/ssd/bidding-data/archive")
        print("  - 日志文件: /Volumes/ssd/bidding-data/logs")
        print()
        print("下一步: 启动后端服务")
        print("  python3 main.py")
    else:
        print("❌ 数据库初始化失败")
        return 1
    print("="*60)
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
