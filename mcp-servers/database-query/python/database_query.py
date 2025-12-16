#!/usr/bin/env python3
"""
Database Query MCP Server

提供标准化的数据库访问接口，支持:
1. 文件信息查询
2. 文件搜索
3. 自动路径转换（容器路径 ↔ 宿主机路径）
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# 添加父目录到路径以便导入共享模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

try:
    import asyncpg
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError as e:
    print(f"Error: Missing required package: {e}", file=sys.stderr)
    print("Install with: pip install mcp asyncpg", file=sys.stderr)
    sys.exit(1)


class PathMapper:
    """路径映射工具：容器路径 ↔ 宿主机路径"""
    
    CONTAINER_PREFIX = "/app/data"
    HOST_PREFIX = "/Volumes/ssd/bidding-data"
    
    @staticmethod
    def to_host_path(container_path: str) -> str:
        """容器路径 → 宿主机路径（用于外部程序访问）"""
        if not container_path:
            return container_path
        return container_path.replace(
            PathMapper.CONTAINER_PREFIX, 
            PathMapper.HOST_PREFIX
        )
    
    @staticmethod
    def to_container_path(host_path: str) -> str:
        """宿主机路径 → 容器路径（用于存储）"""
        if not host_path:
            return host_path
        return host_path.replace(
            PathMapper.HOST_PREFIX,
            PathMapper.CONTAINER_PREFIX
        )
    
    @staticmethod
    def convert_paths_in_result(result: Dict[str, Any], to_host: bool = True) -> Dict[str, Any]:
        """转换结果字典中的路径字段"""
        path_fields = ['file_path', 'archive_path', 'temp_path']
        
        for field in path_fields:
            if field in result and result[field]:
                if to_host:
                    result[field] = PathMapper.to_host_path(result[field])
                else:
                    result[field] = PathMapper.to_container_path(result[field])
        
        return result


class DatabaseQueryServer:
    """数据库查询MCP服务器"""
    
    def __init__(self):
        self.server = Server("bidding-database")
        self.db_pool: Optional[asyncpg.Pool] = None
        
        # 从环境变量读取数据库配置
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5433')),
            'database': os.getenv('DB_NAME', 'bidding_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres123'),
        }
        
        # 注册工具
        self.setup_tools()
        # 注册处理器
        self.setup_handlers()
    
    def setup_tools(self):
        """注册MCP工具"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="query_file_by_id",
                    description="根据文件ID查询文件信息，支持自动路径转换",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_id": {
                                "type": "string",
                                "description": "文件UUID"
                            },
                            "return_host_path": {
                                "type": "boolean",
                                "description": "是否返回宿主机路径（默认true，用于外部程序访问）",
                                "default": True
                            }
                        },
                        "required": ["file_id"]
                    }
                ),
                Tool(
                    name="search_files",
                    description="搜索文件，支持多条件过滤和路径转换",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "文件名关键词（模糊搜索）"
                            },
                            "category": {
                                "type": "string",
                                "description": "文件分类：tender/proposal/reference/financial_reports/certificate/other"
                            },
                            "doc_type": {
                                "type": "string",
                                "description": "文档类型：tender/proposal/reference/other"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "开始日期 (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "结束日期 (YYYY-MM-DD)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回结果数量限制（默认10，最大100）",
                                "default": 10
                            },
                            "return_host_path": {
                                "type": "boolean",
                                "description": "是否返回宿主机路径（默认true）",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="get_file_stats",
                    description="获取文件统计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="list_recent_files",
                    description="列出最近上传的文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "返回数量（默认20）",
                                "default": 20
                            },
                            "return_host_path": {
                                "type": "boolean",
                                "description": "是否返回宿主机路径",
                                "default": True
                            }
                        }
                    }
                )
            ]
    
    def setup_handlers(self):
        """注册工具调用处理器"""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            try:
                if name == "query_file_by_id":
                    result = await self.query_file_by_id(
                        arguments["file_id"],
                        arguments.get("return_host_path", True)
                    )
                elif name == "search_files":
                    result = await self.search_files(
                        filename=arguments.get("filename"),
                        category=arguments.get("category"),
                        doc_type=arguments.get("doc_type"),
                        date_from=arguments.get("date_from"),
                        date_to=arguments.get("date_to"),
                        limit=arguments.get("limit", 10),
                        return_host_path=arguments.get("return_host_path", True)
                    )
                elif name == "get_file_stats":
                    result = await self.get_file_stats()
                elif name == "list_recent_files":
                    result = await self.list_recent_files(
                        limit=arguments.get("limit", 20),
                        return_host_path=arguments.get("return_host_path", True)
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                import json
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]
            
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}\n\nDetails:\n{error_detail}"
                )]
    
    async def ensure_db_pool(self):
        """确保数据库连接池已初始化"""
        if self.db_pool is None:
            self.db_pool = await asyncpg.create_pool(**self.db_config)
    
    async def query_file_by_id(self, file_id: str, return_host_path: bool = True) -> Dict[str, Any]:
        """根据文件ID查询文件信息"""
        await self.ensure_db_pool()
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    id, filename, filetype, doc_type, category,
                    file_path, archive_path, temp_path,
                    file_size, sha256, status, uploader,
                    semantic_filename, version,
                    created_at, parsed_at, archived_at, indexed_at,
                    metadata, error_log
                FROM uploaded_files
                WHERE id = $1
            """, file_id)
            
            if not row:
                raise ValueError(f"File not found: {file_id}")
            
            result = dict(row)
            
            # 转换时间戳为ISO格式
            for field in ['created_at', 'parsed_at', 'archived_at', 'indexed_at']:
                if result.get(field):
                    result[field] = result[field].isoformat()
            
            # 转换文件大小为MB
            if result.get('file_size'):
                result['size_mb'] = round(result['file_size'] / (1024 * 1024), 2)
            
            # 路径转换
            result = PathMapper.convert_paths_in_result(result, to_host=return_host_path)
            
            return result
    
    async def search_files(
        self,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        doc_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 10,
        return_host_path: bool = True
    ) -> Dict[str, Any]:
        """搜索文件"""
        await self.ensure_db_pool()
        
        # 构建查询条件
        conditions = []
        params = []
        param_count = 0
        
        if filename:
            param_count += 1
            conditions.append(f"(filename ILIKE ${param_count} OR semantic_filename ILIKE ${param_count})")
            params.append(f"%{filename}%")
        
        if category:
            param_count += 1
            conditions.append(f"category = ${param_count}")
            params.append(category)
        
        if doc_type:
            param_count += 1
            conditions.append(f"doc_type = ${param_count}")
            params.append(doc_type)
        
        if date_from:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(date_from)
        
        if date_to:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(date_to)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        # 限制结果数量
        limit = min(limit, 100)
        param_count += 1
        params.append(limit)
        
        query = f"""
            SELECT 
                id, filename, filetype, doc_type, category,
                file_path, archive_path,
                file_size, status, uploader,
                semantic_filename, version,
                created_at, archived_at
            FROM uploaded_files
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count}
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            files = []
            for row in rows:
                result = dict(row)
                
                # 转换时间戳
                for field in ['created_at', 'archived_at']:
                    if result.get(field):
                        result[field] = result[field].isoformat()
                
                # 转换文件大小
                if result.get('file_size'):
                    result['size_mb'] = round(result['file_size'] / (1024 * 1024), 2)
                
                # 路径转换
                result = PathMapper.convert_paths_in_result(result, to_host=return_host_path)
                
                files.append(result)
            
            return {
                "total": len(files),
                "files": files
            }
    
    async def get_file_stats(self) -> Dict[str, Any]:
        """获取文件统计信息"""
        await self.ensure_db_pool()
        
        async with self.db_pool.acquire() as conn:
            # 总体统计
            total_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_files,
                    COUNT(DISTINCT doc_type) as doc_types,
                    COUNT(DISTINCT category) as categories,
                    SUM(file_size) as total_size,
                    AVG(file_size) as avg_size
                FROM uploaded_files
            """)
            
            # 按分类统计
            category_stats = await conn.fetch("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    SUM(file_size) as total_size
                FROM uploaded_files
                GROUP BY category
                ORDER BY count DESC
            """)
            
            # 按文档类型统计
            doctype_stats = await conn.fetch("""
                SELECT 
                    doc_type,
                    COUNT(*) as count
                FROM uploaded_files
                GROUP BY doc_type
                ORDER BY count DESC
            """)
            
            return {
                "total_files": total_stats['total_files'],
                "total_size_mb": round(total_stats['total_size'] / (1024 * 1024), 2) if total_stats['total_size'] else 0,
                "avg_size_mb": round(total_stats['avg_size'] / (1024 * 1024), 2) if total_stats['avg_size'] else 0,
                "by_category": [dict(row) for row in category_stats],
                "by_doc_type": [dict(row) for row in doctype_stats]
            }
    
    async def list_recent_files(self, limit: int = 20, return_host_path: bool = True) -> Dict[str, Any]:
        """列出最近上传的文件"""
        await self.ensure_db_pool()
        
        limit = min(limit, 100)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, filename, category, doc_type,
                    file_path, archive_path,
                    file_size, status,
                    created_at
                FROM uploaded_files
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
            
            files = []
            for row in rows:
                result = dict(row)
                
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].isoformat()
                
                if result.get('file_size'):
                    result['size_mb'] = round(result['file_size'] / (1024 * 1024), 2)
                
                result = PathMapper.convert_paths_in_result(result, to_host=return_host_path)
                
                files.append(result)
            
            return {
                "total": len(files),
                "files": files
            }
    
    async def cleanup(self):
        """清理资源"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def run(self):
        """运行MCP服务器"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """主函数"""
    server = DatabaseQueryServer()
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
