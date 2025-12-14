"""
数据库连接管理模块
提供PostgreSQL连接、查询和事务管理功能
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os


class DatabaseConnection:
    """PostgreSQL数据库连接管理类"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5433)),
            database=os.getenv("DB_NAME", "bidding_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres123")
        )
        self.conn.autocommit = False
    
    def query(self, sql, params=None):
        """
        执行查询并返回所有结果(转为字典列表)
        
        Args:
            sql: SQL查询语句
            params: 参数元组
            
        Returns:
            list: 字典列表,每个字典代表一行数据
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params or ())
                results = cursor.fetchall()
                # 转换为普通字典列表
                return [dict(row) for row in results] if results else []
        except Exception:
            self.conn.rollback()
            raise
    
    def query_one(self, sql, params=None):
        """
        执行查询并返回单条结果(转为字典)
        
        Args:
            sql: SQL查询语句
            params: 参数元组
            
        Returns:
            dict or None: 单条数据字典,无结果返回None
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params or ())
                result = cursor.fetchone()
                # 转换为普通字典
                return dict(result) if result else None
        except Exception:
            self.conn.rollback()
            raise

    def query_all(self, sql, params=None):
        """与 query 功能相同，提供向后兼容的接口名称"""
        return self.query(sql, params)
    
    def execute(self, sql, params=None):
        """
        执行写操作(INSERT/UPDATE/DELETE),返回受影响的行ID或None
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            str or int or None: INSERT ... RETURNING id返回的ID,否则返回None
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                self.conn.commit()
                # 如果是 INSERT ... RETURNING id,返回该ID
                if cursor.description:
                    result = cursor.fetchone()
                    return result[0] if result else None
                return None
        except Exception:
            self.conn.rollback()
            raise
    
    def execute_many(self, sql, params_list):
        """
        批量执行写操作
        
        Args:
            sql: SQL语句
            params_list: 参数列表,每个元素是一个参数元组
            
        Returns:
            int: 受影响的行数
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.executemany(sql, params_list)
                self.conn.commit()
                return cursor.rowcount
        except Exception:
            self.conn.rollback()
            raise
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        用法:
            with db.transaction():
                db.execute("INSERT ...")
                db.execute("UPDATE ...")
        """
        try:
            yield self
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


# 全局单例
db = DatabaseConnection()
