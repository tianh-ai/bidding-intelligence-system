# -*- coding: utf-8 -*-
"""
enhanced_database.py - 增强的数据库初始化脚本
包含关系逻辑追踪表，用于记录verify_new_parser和parsing_results的完整关系
"""

import asyncio
import asyncpg
import os
from datetime import datetime
from loguru import logger

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "bidding_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

logger.add(
    "/Volumes/ssd/bidding-data/logs/enhanced_database.log",
    rotation="500 MB",
    level="INFO"
)


async def get_db_connection():
    """获取异步数据库连接"""
    return await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


async def create_uploaded_files_table(db):
    """创建上传文件追踪表（核心枢纽表）"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            file_size BIGINT,
            upload_status TEXT DEFAULT 'pending',  -- pending|completed|failed
            parse_status TEXT DEFAULT 'pending',   -- pending|processing|completed|failed
            storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data/uploads',
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
    """创建解析结果表（存储verify_new_parser的输出）"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS parsing_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
            
            -- 解析基础信息
            chapter_count INTEGER,
            parsing_time FLOAT,
            parsing_status TEXT DEFAULT 'pending',  -- pending|completed|failed
            error_message TEXT,
            
            -- 存储完整的verify_new_parser结果
            result_json JSONB DEFAULT NULL,
            
            -- verify_new_parser输出的核心指标
            accuracy_score FLOAT DEFAULT NULL,  -- 成功率 (87.5)
            matched_toc_items INTEGER DEFAULT NULL,  -- 匹配项数 (14)
            total_toc_items INTEGER DEFAULT NULL,  -- 总TOC项数 (16)
            
            storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data/parsed',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ parsing_results 表已创建")
        
        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_parsing_results_file_id 
            ON parsing_results(file_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_parsing_results_accuracy
            ON parsing_results(accuracy_score)
        """)
        
    except Exception as e:
        logger.warning(f"parsing_results 表可能已存在: {e}")


async def create_knowledge_base_table(db):
    """创建知识库表（从解析结果提取的知识条项）"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
            
            -- 知识条项内容
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            category VARCHAR(100),
            
            -- 溯源信息
            file_name VARCHAR(255),
            source VARCHAR(100),
            chapter_source VARCHAR(255),  -- 来自哪个章节 (e.g., "第一部分")
            
            -- 提取质量指标
            extraction_confidence FLOAT DEFAULT 1.0,  -- 0-1 置信度
            
            -- AI增强
            embedding vector(1536),
            
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


async def create_verification_tracking_table(db):
    """创建验证追踪表（记录verify_new_parser的每一次执行）
    
    这个表用于追踪每个文件的验证过程，包括：
    - verify_new_parser的执行结果
    - 与parsing_results的关系
    - 验证的详细细节
    """
    try:
        query = """
        CREATE TABLE IF NOT EXISTS verification_tracking (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- 关键关系
            file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
            parsing_result_id UUID REFERENCES parsing_results(id) ON DELETE CASCADE,
            
            -- 验证过程信息
            verification_status TEXT DEFAULT 'pending',  -- pending|completed|failed
            verification_start_time TIMESTAMPTZ,
            verification_end_time TIMESTAMPTZ,
            verification_duration_seconds FLOAT,
            
            -- 验证结果详情 (从verify_new_parser.py)
            total_toc_items INTEGER NOT NULL,  -- 参考TOC项总数 (16)
            matched_toc_items INTEGER NOT NULL,  -- 成功匹配项数 (14)
            success_rate FLOAT NOT NULL,  -- 成功率百分比 (87.5)
            
            -- 章节提取统计
            extracted_chapter_count INTEGER,  -- 实际提取的章节数 (24)
            
            -- 每项TOC的验证详情 (JSONB数组)
            toc_verification_details JSONB DEFAULT NULL,
            
            -- 失败项的详情
            failed_items JSONB DEFAULT NULL,
            
            -- 错误和日志
            error_message TEXT DEFAULT NULL,
            verification_log TEXT DEFAULT NULL,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ verification_tracking 表已创建")
        
        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_tracking_file_id 
            ON verification_tracking(file_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_tracking_parsing_result_id 
            ON verification_tracking(parsing_result_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_tracking_status 
            ON verification_tracking(verification_status)
        """)
        
    except Exception as e:
        logger.warning(f"verification_tracking 表可能已存在: {e}")


async def create_parsing_to_verification_junction_table(db):
    """创建parsing_results与verification_tracking的关系表
    
    用于详细追踪两个验证脚本之间的数据流和依赖关系
    """
    try:
        query = """
        CREATE TABLE IF NOT EXISTS parsing_verification_mapping (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- 关键关系
            file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
            parsing_result_id UUID NOT NULL REFERENCES parsing_results(id) ON DELETE CASCADE,
            verification_tracking_id UUID NOT NULL REFERENCES verification_tracking(id) ON DELETE CASCADE,
            
            -- 流程信息
            parse_to_verify_delay_seconds FLOAT,  -- 解析完成到验证开始的延迟
            data_flow_path TEXT,  -- 数据流路径描述
            
            -- 验证对标
            parser_accuracy_vs_verify_score JSONB,  -- 对比信息
            
            -- 质量评估
            overall_quality_score FLOAT,  -- 0-1 综合质量评分
            quality_comments TEXT,
            
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ parsing_verification_mapping 表已创建")
        
        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_parsing_verification_mapping_file_id 
            ON parsing_verification_mapping(file_id)
        """)
        
    except Exception as e:
        logger.warning(f"parsing_verification_mapping 表可能已存在: {e}")


async def create_relationships_documentation_table(db):
    """创建关系逻辑文档表
    
    记录系统中各表之间的关系定义和数据流规则
    """
    try:
        query = """
        CREATE TABLE IF NOT EXISTS relationships_documentation (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- 关系定义
            source_table VARCHAR(255) NOT NULL,
            target_table VARCHAR(255) NOT NULL,
            relationship_type VARCHAR(50) NOT NULL,  -- 1:1, 1:N, N:1, N:N
            
            -- 关联字段
            source_field VARCHAR(255),
            target_field VARCHAR(255),
            foreign_key_name VARCHAR(255),
            
            -- 数据流信息
            data_flow_direction VARCHAR(50),  -- source_to_target, bidirectional
            transformation_logic TEXT,  -- 数据转换逻辑
            
            -- 时序关系
            execution_order INTEGER,  -- 执行顺序
            depends_on TEXT,  -- 依赖的其他关系
            
            -- 约束规则
            cascade_on_delete BOOLEAN DEFAULT FALSE,
            unique_constraint BOOLEAN DEFAULT FALSE,
            
            -- 文档
            description TEXT,
            examples TEXT,
            notes TEXT,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ relationships_documentation 表已创建")
        
    except Exception as e:
        logger.warning(f"relationships_documentation 表可能已存在: {e}")


async def insert_relationship_documentation(db):
    """插入关系文档数据"""
    try:
        relationships = [
            # 关系1: uploaded_files → parsing_results
            {
                "source_table": "uploaded_files",
                "target_table": "parsing_results",
                "relationship_type": "1:1",
                "source_field": "id",
                "target_field": "file_id",
                "foreign_key_name": "fk_parsing_results_file_id",
                "data_flow_direction": "source_to_target",
                "transformation_logic": "一个上传的文件产生一条解析结果",
                "execution_order": 1,
                "depends_on": "None",
                "cascade_on_delete": True,
                "description": "文件上传后触发解析，生成parsing_results记录",
                "examples": "user uploads PDF → parsing_results record created with file_id reference"
            },
            # 关系2: uploaded_files → knowledge_base
            {
                "source_table": "uploaded_files",
                "target_table": "knowledge_base",
                "relationship_type": "1:N",
                "source_field": "id",
                "target_field": "file_id",
                "foreign_key_name": "fk_knowledge_base_file_id",
                "data_flow_direction": "source_to_target",
                "transformation_logic": "一个文件的解析结果被分解为多个知识条项",
                "execution_order": 3,
                "depends_on": "parsing_results",
                "cascade_on_delete": True,
                "description": "从parsing_results提取知识条项，关联回源文件"
            },
            # 关系3: verify_new_parser → parsing_results
            {
                "source_table": "verify_new_parser",
                "target_table": "parsing_results",
                "relationship_type": "1:1",
                "source_field": "verification_output",
                "target_field": "result_json",
                "data_flow_direction": "source_to_target",
                "transformation_logic": "verify脚本验证输出保存为JSON",
                "execution_order": 2,
                "depends_on": "uploaded_files → parsing_results",
                "description": "verify_new_parser验证结果直接存入parsing_results.result_json",
                "examples": "verify output: {accuracy_score: 87.5, matched: 14, total: 16} → stored in result_json"
            },
            # 关系4: parsing_results → verification_tracking
            {
                "source_table": "parsing_results",
                "target_table": "verification_tracking",
                "relationship_type": "1:1",
                "source_field": "id",
                "target_field": "parsing_result_id",
                "data_flow_direction": "source_to_target",
                "transformation_logic": "每个解析结果有一条对应的验证追踪记录",
                "execution_order": 2,
                "depends_on": "uploaded_files → parsing_results",
                "description": "记录verify_new_parser的执行过程和结果"
            }
        ]
        
        for rel in relationships:
            query = """
            INSERT INTO relationships_documentation 
            (source_table, target_table, relationship_type, source_field, target_field,
             foreign_key_name, data_flow_direction, transformation_logic, execution_order,
             depends_on, cascade_on_delete, description, examples)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT DO NOTHING
            """
            await db.execute(query,
                rel["source_table"],
                rel["target_table"],
                rel["relationship_type"],
                rel.get("source_field"),
                rel.get("target_field"),
                rel.get("foreign_key_name"),
                rel["data_flow_direction"],
                rel["transformation_logic"],
                rel["execution_order"],
                rel.get("depends_on"),
                rel["cascade_on_delete"],
                rel["description"],
                rel.get("examples")
            )
        
        logger.info("✓ 关系文档已插入")
        
    except Exception as e:
        logger.warning(f"插入关系文档失败: {e}")


async def init_database():
    """主初始化函数"""
    try:
        db = await get_db_connection()
        logger.info("✓ 数据库连接成功")
        
        # Step 1: 创建基础表（按依赖顺序）
        await create_uploaded_files_table(db)
        await create_parsing_results_table(db)
        await create_knowledge_base_table(db)
        
        # Step 2: 创建关系追踪表
        await create_verification_tracking_table(db)
        await create_parsing_to_verification_junction_table(db)
        
        # Step 3: 创建关系文档表
        await create_relationships_documentation_table(db)
        await insert_relationship_documentation(db)
        
        await db.close()
        logger.info("✓ 所有表创建完成")
        return True
        
    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {e}")
        return False


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
    print("="*70)
    print("🚀 增强数据库初始化 (含关系追踪)")
    print("="*70)
    print()
    
    # 验证存储路径
    await verify_storage_paths()
    print()
    
    # 初始化数据库
    success = await init_database()
    
    print()
    print("="*70)
    if success:
        print("✅ 增强数据库初始化完成！")
        print()
        print("新增表:")
        print("  1. verification_tracking - 验证追踪表")
        print("  2. parsing_verification_mapping - 解析-验证映射表")
        print("  3. relationships_documentation - 关系文档表")
        print()
        print("核心表:")
        print("  1. uploaded_files - 文件追踪 (核心枢纽)")
        print("  2. parsing_results - 解析结果 (verify输出)")
        print("  3. knowledge_base - 知识库 (提取内容)")
        print()
        print("数据流:")
        print("  PDF上传 → uploaded_files")
        print("       ↓")
        print("  verify_new_parser.py执行")
        print("       ↓")
        print("  parsing_results (含verify结果)")
        print("       ↓")
        print("  knowledge_base (多条记录)")
        print()
        print("存储配置:")
        print("  - 文件上传: /Volumes/ssd/bidding-data/uploads")
        print("  - 解析结果: /Volumes/ssd/bidding-data/parsed")
        print("  - 日志文件: /Volumes/ssd/bidding-data/logs")
        print()
    else:
        print("❌ 数据库初始化失败")
        return 1
    print("="*70)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
