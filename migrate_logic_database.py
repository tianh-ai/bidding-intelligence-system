"""
数据库迁移脚本：创建统一的logic_database表
此脚本将新的logic_database表添加到现有数据库
"""

import psycopg2
from psycopg2.extras import DictCursor
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from core.config import get_settings
from core.logger import logger


def run_migration():
    """运行迁移"""
    settings = get_settings()
    
    conn = None
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # 创建统一的逻辑规则数据库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logic_database (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                
                -- 基本属性
                rule_type text NOT NULL CHECK (rule_type IN (
                    'structure', 'content', 'mandatory', 'scoring', 
                    'consistency', 'formatting', 'terminology'
                )),
                priority text NOT NULL DEFAULT 'medium' CHECK (priority IN (
                    'critical', 'high', 'medium', 'low'
                )),
                source text NOT NULL CHECK (source IN (
                    'chapter_learning', 'global_learning', 'manual', 'report_analysis'
                )),
                
                -- 规则条件
                condition jsonb DEFAULT NULL,
                condition_description text NOT NULL,
                
                -- 规则内容
                description text NOT NULL,
                pattern text DEFAULT NULL,
                
                -- 规则动作
                action jsonb DEFAULT NULL,
                action_description text NOT NULL,
                
                -- 定量约束
                constraints jsonb DEFAULT NULL,
                
                -- 规则覆盖范围
                scope jsonb DEFAULT NULL,
                
                -- 元数据
                confidence decimal DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
                version int DEFAULT 1,
                tags text[] DEFAULT '{}',
                
                -- 参考信息（追踪规则来源）
                reference jsonb DEFAULT NULL,
                
                -- 检查建议
                fix_suggestion text DEFAULT NULL,
                
                -- 示例
                examples text[] DEFAULT '{}',
                counter_examples text[] DEFAULT '{}',
                
                -- 时间戳
                created_at timestamptz DEFAULT now(),
                updated_at timestamptz DEFAULT now(),
                
                -- 状态
                is_active boolean DEFAULT TRUE
            );
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logic_database_type ON logic_database(rule_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logic_database_priority ON logic_database(priority);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logic_database_source ON logic_database(source);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logic_database_scope ON logic_database USING GIN(scope);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logic_database_created_at ON logic_database(created_at DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logic_database_active ON logic_database(is_active);")
        
        # 更新logic_versions表（如果存在）
        cursor.execute("""
            ALTER TABLE IF EXISTS logic_versions
            ADD COLUMN IF NOT EXISTS rule_ids uuid[] DEFAULT '{}';
        """)
        
        conn.commit()
        logger.info("✅ Migration completed: logic_database table created successfully")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise
    
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    run_migration()
