"""
Knowledge Base MCP - Python Backend
提供知识库查询、向量搜索、知识条目管理功能
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

# 导入主程序的数据库和配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'backend'))

from database import db
from core.logger import logger
from core.ollama_client import get_ollama_client
from core.config import get_settings


class KnowledgeBaseMCP:
    """知识库 MCP 服务"""
    
    def __init__(self):
        """初始化知识库服务"""
        self.db = db
        self.settings = get_settings()
        self.use_ollama = self.settings.USE_OLLAMA_FOR_EMBEDDINGS
        self._kb_columns: Optional[set[str]] = None
        self._uploaded_files_columns: Optional[set[str]] = None
        if self.use_ollama:
            self.ollama_client = get_ollama_client()
        logger.info(f"KnowledgeBaseMCP initialized (Ollama: {self.use_ollama})")

    def _get_table_columns(self, table_name: str) -> set[str]:
        try:
            rows = self.db.query(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                """,
                (table_name,),
            ) or []
            return {r.get("column_name") for r in rows if r.get("column_name")}
        except Exception as e:
            logger.warning(f"读取表字段失败({table_name}): {e}")
            return set()

    def _kb_has(self, col: str) -> bool:
        if self._kb_columns is None:
            self._kb_columns = self._get_table_columns("knowledge_base")
        return col in self._kb_columns

    def _uploaded_files_has(self, col: str) -> bool:
        if self._uploaded_files_columns is None:
            self._uploaded_files_columns = self._get_table_columns("uploaded_files")
        return col in self._uploaded_files_columns
    
    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库条目
        
        Args:
            query: 搜索关键词
            category: 分类过滤 (tender/proposal/reference)
            limit: 返回数量限制
            min_score: 最小相似度分数
            
        Returns:
            知识条目列表
        """
        try:
            conditions = ["content LIKE %s"]
            params = [f"%{query}%"]
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            where_clause = " AND ".join(conditions)

            select_cols = [
                "id",
                "file_id",
                "category",
                "title",
                "content",
                "created_at",
            ]
            if self._kb_has("keywords"):
                select_cols.insert(5, "keywords")
            if self._kb_has("importance_score"):
                select_cols.insert(6 if self._kb_has("keywords") else 5, "importance_score")

            order_by = "created_at DESC"
            if self._kb_has("importance_score"):
                order_by = "importance_score DESC, created_at DESC"
            
            query_sql = f"""
                SELECT 
                    {', '.join(select_cols)}
                FROM knowledge_base
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT %s
            """
            params.append(limit)
            
            results = self.db.query(query_sql, tuple(params)) or []
            
            return [
                {
                    "id": row["id"],
                    "file_id": row["file_id"],
                    "category": row["category"],
                    "title": row["title"],
                    "content": row["content"],
                    "keywords": json.loads(row["keywords"]) if self._kb_has("keywords") and row.get("keywords") else [],
                    "importance_score": float(row["importance_score"]) if self._kb_has("importance_score") and row.get("importance_score") else 0.0,
                    "created_at": str(row["created_at"])
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []
    
    def search_knowledge_semantic(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        语义向量搜索知识库
        
        Args:
            query: 搜索查询
            category: 分类过滤
            limit: 返回数量限制
            min_similarity: 最小相似度阈值 (0-1)
            
        Returns:
            知识条目列表（按相似度排序）
        """
        try:
            if not self.use_ollama:
                logger.warning("Ollama embeddings not enabled, falling back to keyword search")
                return self.search_knowledge(query, category, limit)

            if not self._kb_has("embedding"):
                logger.warning(
                    "Semantic search requested but knowledge_base.embedding column is missing; "
                    "run migration to add embedding column to enable semantic search"
                )
                return []
            
            # 1. 生成查询向量
            import asyncio
            query_embedding = asyncio.run(self.ollama_client.generate_embedding(query))
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return self.search_knowledge(query, category, limit)
            
            # 2. 构建 SQL 查询
            conditions = ["embedding IS NOT NULL"]
            params = [query_embedding]
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            where_clause = " AND ".join(conditions)
            
            # 3. 向量相似度搜索（余弦距离）
            select_cols = [
                "id",
                "file_id",
                "category",
                "title",
                "content",
                "created_at",
            ]
            if self._kb_has("keywords"):
                select_cols.insert(5, "keywords")
            if self._kb_has("importance_score"):
                select_cols.insert(6 if self._kb_has("keywords") else 5, "importance_score")

            query_sql = f"""
                SELECT 
                    {', '.join(select_cols)},
                    1 - (embedding <=> %s::vector) as similarity
                FROM knowledge_base
                WHERE {where_clause}
                    AND 1 - (embedding <=> %s::vector) > %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            
            params.extend([query_embedding, min_similarity, query_embedding, limit])
            results = self.db.query(query_sql, tuple(params)) or []
            
            logger.info(f"Semantic search found {len(results)} results")
            
            return [
                {
                    "id": row["id"],
                    "file_id": row["file_id"],
                    "category": row["category"],
                    "title": row["title"],
                    "content": row["content"],
                    "keywords": json.loads(row["keywords"]) if self._kb_has("keywords") and row.get("keywords") else [],
                    "importance_score": float(row["importance_score"]) if self._kb_has("importance_score") and row.get("importance_score") else 0.0,
                    "similarity": float(row["similarity"]),
                    "created_at": str(row["created_at"])
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            # 回退到关键词搜索
            return self.search_knowledge(query, category, limit)
    
    def add_knowledge_entry(
        self,
        file_id: str,
        category: str,
        title: str,
        content: str,
        keywords: Optional[List[str]] = None,
        importance_score: float = 50.0,
        metadata: Optional[Dict[str, Any]] = None,
        auto_embed: bool = True
    ) -> Dict[str, Any]:
        """
        添加知识库条目（自动生成向量嵌入）
        
        Args:
            file_id: 文件ID
            category: 分类 (tender/proposal/reference)
            title: 标题
            content: 内容
            keywords: 关键词列表
            importance_score: 重要性分数 (0-100)
            metadata: 元数据
            auto_embed: 是否自动生成向量嵌入
            
        Returns:
            创建的条目信息
        """
        try:
            import uuid
            import asyncio
            
            entry_id = str(uuid.uuid4())
            keywords_json = json.dumps(keywords or [], ensure_ascii=False)
            metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
            
            # 生成向量嵌入
            embedding = None
            if auto_embed and self.use_ollama:
                try:
                    # 组合标题和内容生成嵌入
                    embed_text = f"{title}\n{content}"
                    embedding = asyncio.run(self.ollama_client.generate_embedding(embed_text))
                    logger.info(f"Generated embedding: {len(embedding)} dimensions")
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")
            
            # 插入数据库（兼容不同 schema：某些部署没有 keywords/importance_score/metadata 字段）
            insert_cols = ["id", "file_id", "category", "title", "content"]
            insert_vals: List[Any] = [entry_id, file_id, category, title, content]

            if self._kb_has("keywords"):
                insert_cols.append("keywords")
                insert_vals.append(keywords_json)
            if self._kb_has("importance_score"):
                insert_cols.append("importance_score")
                insert_vals.append(importance_score)
            if self._kb_has("metadata"):
                insert_cols.append("metadata")
                insert_vals.append(metadata_json)
            if embedding and self._kb_has("embedding"):
                insert_cols.append("embedding")
                insert_vals.append(embedding)

            # source/file_name 只有在表里存在时才写入
            if self._kb_has("source"):
                insert_cols.append("source")
                insert_vals.append("manual")

            col_sql = ", ".join(insert_cols)
            ph_sql = ", ".join(["%s"] * len(insert_cols))
            self.db.execute(
                f"INSERT INTO knowledge_base ({col_sql}) VALUES ({ph_sql})",
                tuple(insert_vals),
            )
            
            return {
                "id": entry_id,
                "file_id": file_id,
                "category": category,
                "title": title,
                "success": True,
                "message": "知识条目已创建"
            }
        except Exception as e:
            logger.error(f"添加知识条目失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_knowledge_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        获取知识库条目详情
        
        Args:
            entry_id: 条目ID
            
        Returns:
            条目详情
        """
        try:
            kb_select = [
                "kb.id",
                "kb.file_id",
                "kb.category",
                "kb.title",
                "kb.content",
                "kb.created_at",
            ]
            if self._kb_has("keywords"):
                kb_select.insert(5, "kb.keywords")
            if self._kb_has("importance_score"):
                kb_select.insert(6 if self._kb_has("keywords") else 5, "kb.importance_score")
            if self._kb_has("metadata"):
                kb_select.append("kb.metadata")

            uf_select = []
            if self._uploaded_files_has("semantic_filename"):
                uf_select.append("uf.semantic_filename")
            if self._uploaded_files_has("filename"):
                uf_select.append("uf.filename")
            if self._uploaded_files_has("file_name"):
                uf_select.append("uf.file_name")

            select_all = kb_select + uf_select

            row = self.db.query_one(
                f"""
                SELECT {', '.join(select_all)}
                FROM knowledge_base kb
                LEFT JOIN uploaded_files uf ON kb.file_id = uf.id
                WHERE kb.id = %s
                """,
                (entry_id,),
            )
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "file_id": row["file_id"],
                "filename": row.get("semantic_filename") or row.get("filename") or row.get("file_name"),
                "category": row["category"],
                "title": row["title"],
                "content": row["content"],
                "keywords": json.loads(row["keywords"]) if self._kb_has("keywords") and row.get("keywords") else [],
                "importance_score": float(row["importance_score"]) if self._kb_has("importance_score") and row.get("importance_score") else 0.0,
                "metadata": json.loads(row["metadata"]) if self._kb_has("metadata") and row.get("metadata") else {},
                "created_at": str(row["created_at"])
            }
        except Exception as e:
            logger.error(f"获取知识条目失败: {e}")
            return None
    
    def list_knowledge_entries(
        self,
        file_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        列出知识库条目
        
        Args:
            file_id: 文件ID过滤
            category: 分类过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            条目列表和统计信息
        """
        try:
            conditions = []
            params = []
            
            if file_id:
                conditions.append("file_id = %s")
                params.append(file_id)
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM knowledge_base WHERE {where_clause}"
            count_result = self.db.query_one(count_sql, tuple(params))
            total = count_result["total"] if count_result else 0
            
            # 获取列表
            select_cols = [
                "id",
                "file_id",
                "category",
                "title",
                "content",
                "created_at",
            ]
            if self._kb_has("keywords"):
                select_cols.insert(5, "keywords")
            if self._kb_has("importance_score"):
                select_cols.insert(6 if self._kb_has("keywords") else 5, "importance_score")

            order_by = "created_at DESC"
            if self._kb_has("importance_score"):
                order_by = "importance_score DESC, created_at DESC"

            list_sql = f"""
                SELECT {', '.join(select_cols)}
                FROM knowledge_base
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            results = self.db.query(list_sql, tuple(params)) or []
            
            entries = [
                {
                    "id": row["id"],
                    "file_id": row["file_id"],
                    "category": row["category"],
                    "title": row["title"],
                    "content_preview": row["content"][:200] if row["content"] else "",
                    "keywords": json.loads(row["keywords"]) if self._kb_has("keywords") and row.get("keywords") else [],
                    "importance_score": float(row["importance_score"]) if self._kb_has("importance_score") and row.get("importance_score") else 0.0,
                    "created_at": str(row["created_at"])
                }
                for row in results
            ]
            
            return {
                "entries": entries,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"列出知识条目失败: {e}")
            return {
                "entries": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "error": str(e)
            }
    
    def delete_knowledge_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        删除知识库条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            操作结果
        """
        try:
            self.db.execute(
                "DELETE FROM knowledge_base WHERE id = %s",
                (entry_id,)
            )
            
            return {
                "success": True,
                "message": f"知识条目 {entry_id} 已删除"
            }
        except Exception as e:
            logger.error(f"删除知识条目失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reindex_embeddings(
        self,
        batch_size: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量重建知识库向量索引
        
        Args:
            batch_size: 批次大小
            category: 仅重建特定分类（可选）
            
        Returns:
            重建结果统计
        """
        try:
            if not self.use_ollama:
                return {
                    "success": False,
                    "error": "Ollama embeddings not enabled"
                }

            if not self._kb_has("embedding"):
                return {
                    "success": False,
                    "error": "knowledge_base.embedding column is missing; cannot reindex embeddings"
                }
            
            import asyncio
            
            # 查询需要重建的条目
            # 注意：vector(1024) 类型不允许 '[]'::vector 这种无维度字面量
            # 统一约定：未生成 embedding 的条目以 NULL 表示
            conditions = ["embedding IS NULL"]
            params = []
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            where_clause = " AND ".join(conditions)
            
            query_sql = f"""
                SELECT id, title, content
                FROM knowledge_base
                WHERE {where_clause}
                ORDER BY created_at DESC
            """
            
            entries = self.db.query(query_sql, tuple(params)) or []
            total = len(entries)
            
            if total == 0:
                return {
                    "success": True,
                    "message": "No entries need reindexing",
                    "total": 0,
                    "processed": 0
                }
            
            logger.info(f"Reindexing {total} entries...")
            
            processed = 0
            failed = 0
            
            # 批量处理
            for i in range(0, total, batch_size):
                batch = entries[i:i + batch_size]
                
                for entry in batch:
                    try:
                        # 生成 embedding
                        embed_text = f"{entry['title']}\n{entry['content']}"
                        embedding = asyncio.run(
                            self.ollama_client.generate_embedding(embed_text)
                        )
                        
                        # 更新数据库
                        self.db.execute(
                            "UPDATE knowledge_base SET embedding = %s WHERE id = %s",
                            (embedding, entry['id'])
                        )
                        
                        processed += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to reindex {entry['id']}: {e}")
                        failed += 1
                
                logger.info(f"Processed {processed}/{total} entries...")
            
            return {
                "success": True,
                "message": "Reindexing completed",
                "total": total,
                "processed": processed,
                "failed": failed
            }
            
        except Exception as e:
            logger.error(f"Reindexing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            统计信息
        """
        try:
            # 总条目数
            total_result = self.db.query_one(
                "SELECT COUNT(*) as total FROM knowledge_base"
            )
            total = total_result["total"] if total_result else 0
            
            # 按分类统计
            category_stats = self.db.query(
                """
                SELECT category, COUNT(*) as count
                FROM knowledge_base
                GROUP BY category
                ORDER BY count DESC
                """
            ) or []
            
            # 最近添加
            recent_entries = self.db.query(
                """
                SELECT id, title, category, created_at
                FROM knowledge_base
                ORDER BY created_at DESC
                LIMIT 10
                """
            ) or []
            
            return {
                "total_entries": total,
                "by_category": {
                    row["category"]: row["count"]
                    for row in category_stats
                },
                "recent_entries": [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "category": row["category"],
                        "created_at": str(row["created_at"])
                    }
                    for row in recent_entries
                ]
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_entries": 0,
                "by_category": {},
                "recent_entries": [],
                "error": str(e)
            }


# CLI 接口（用于测试）
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge Base MCP CLI')
    parser.add_argument('command', choices=['search', 'add', 'get', 'list', 'delete', 'stats'])
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--id', help='Entry ID')
    parser.add_argument('--file-id', help='File ID')
    parser.add_argument('--category', help='Category (tender/proposal/reference)')
    parser.add_argument('--title', help='Entry title')
    parser.add_argument('--content', help='Entry content')
    parser.add_argument('--keywords', help='Keywords (comma-separated)')
    parser.add_argument('--importance', type=float, default=50.0, help='Importance score')
    parser.add_argument('--limit', type=int, default=10, help='Limit')
    parser.add_argument('--offset', type=int, default=0, help='Offset')
    
    args = parser.parse_args()
    
    kb = KnowledgeBaseMCP()
    
    if args.command == 'search':
        if not args.query:
            print("Error: --query required for search")
            sys.exit(1)
        result = kb.search_knowledge(args.query, args.category, args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'add':
        if not all([args.file_id, args.category, args.title, args.content]):
            print("Error: --file-id, --category, --title, --content required")
            sys.exit(1)
        keywords = args.keywords.split(',') if args.keywords else []
        result = kb.add_knowledge_entry(
            args.file_id, args.category, args.title, args.content,
            keywords, args.importance
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'get':
        if not args.id:
            print("Error: --id required")
            sys.exit(1)
        result = kb.get_knowledge_entry(args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'list':
        result = kb.list_knowledge_entries(
            args.file_id, args.category, args.limit, args.offset
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'delete':
        if not args.id:
            print("Error: --id required")
            sys.exit(1)
        result = kb.delete_knowledge_entry(args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'stats':
        result = kb.get_statistics()
        print(json.dumps(result, ensure_ascii=False, indent=2))
