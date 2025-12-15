"""
Logic Learning MCP - Python Backend
提供逻辑学习功能：章节级学习、全局级学习、逻辑规则提取
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import uuid

# 导入主程序的数据库和配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'backend'))

from database import db
from core.logger import logger
from core.config import get_settings
from core.cache import cache  # 使用 Redis 缓存
from engines import ChapterLogicEngine, GlobalLogicEngine

# 任务状态存储 TTL（24小时）
TASK_STATUS_TTL = 86400


class LogicLearningMCP:
    """逻辑学习 MCP 服务"""
    
    def __init__(self):
        """初始化逻辑学习服务"""
        self.db = db
        self.settings = get_settings()
        self.chapter_engine = ChapterLogicEngine()
        self.global_engine = GlobalLogicEngine()
        # 使用 Redis 替代内存存储
        self.cache = cache
        logger.info("LogicLearningMCP initialized")

    def start_learning(
        self,
        file_ids: List[str],
        learning_type: str,
        chapter_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        启动学习任务
        
        Args:
            file_ids: 学习文件ID列表
            learning_type: 学习类型 (chapter/global)
            chapter_ids: 章节ID列表（章节级学习时必填）
            
        Returns:
            任务信息 {"task_id": str, "status": str}
        """
        try:
            task_id = str(uuid.uuid4())
            
            # 初始化任务状态
            task_status = {
                "task_id": task_id,
                "status": "processing",
                "progress": 0,
                "message": "Initializing learning task...",
                "file_ids": file_ids,
                "learning_type": learning_type,
                "chapter_ids": chapter_ids or [],
                "created_at": datetime.now().isoformat(),
            }
            
            # 存储到 Redis
            cache_key = f"learning_task:{task_id}"
            self.cache.set(cache_key, task_status, ttl=TASK_STATUS_TTL)
            
            # 验证文件存在（容错处理）
            try:
                for file_id in file_ids:
                    file_info = self.db.query_one(
                        "SELECT id, filename FROM uploaded_files WHERE id = %s",
                        (file_id,)
                    )
                    if not file_info:
                        logger.warning(f"File {file_id} not found in database")
                        # 继续处理，不抛出错误
            except Exception as e:
                logger.warning(f"File validation failed (continuing anyway): {e}")
            
            # 根据学习类型执行不同逻辑
            if learning_type == "chapter":
                if not chapter_ids:
                    raise ValueError("Chapter IDs required for chapter learning")
                result = self._chapter_learning(task_id, file_ids, chapter_ids)
            elif learning_type == "global":
                result = self._global_learning(task_id, file_ids)
            else:
                raise ValueError(f"Invalid learning type: {learning_type}")
            
            # 更新任务状态为完成
            task_status = self.cache.get(f"learning_task:{task_id}") or {}
            task_status.update({
                "status": "completed",
                "progress": 100,
                "message": "Learning completed successfully",
                "result": result,
                "completed_at": datetime.now().isoformat(),
            })
            self.cache.set(f"learning_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
            
            return {
                "task_id": task_id,
                "status": "processing",
                "message": "Learning task started",
            }
            
        except Exception as e:
            logger.error(f"Start learning failed: {e}", exc_info=True)
            task_status = self.cache.get(f"learning_task:{task_id}") or {}
            task_status.update({
                "status": "failed",
                "message": str(e),
            })
            self.cache.set(f"learning_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
            raise

    def _chapter_learning(
        self,
        task_id: str,
        file_ids: List[str],
        chapter_ids: List[str]
    ) -> Dict[str, Any]:
        """
        章节级学习
        
        分析指定章节的逻辑规则，提取评分标准、必要条件等
        """
        logger.info(f"Chapter learning: task={task_id}, files={file_ids}, chapters={chapter_ids}")
        
        rules_learned = []
        chapters_processed = 0
        for chapter_id in chapter_ids:
            # 更新进度
            progress = int((chapters_processed / len(chapter_ids)) * 100)
            task_status = self.cache.get(f"learning_task:{task_id}") or {}
            task_status["progress"] = progress
            task_status["message"] = f"Processing chapter {chapters_processed + 1}/{len(chapter_ids)}..."
            self.cache.set(f"learning_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
            self.task_store[task_id]["message"] = f"Processing chapter {chapters_processed + 1}/{len(chapter_ids)}..."
            
            # 查询章节信息
            chapter = self.db.query_one(
                """
                SELECT c.id, c.file_id, c.title, c.content, c.level, c.order_index,
                       f.filename, f.filetype as file_type
                FROM document_chapters c
                JOIN uploaded_files f ON c.file_id = f.id
                WHERE c.id = %s
                """,
                (chapter_id,)
            )
            
            if not chapter:
                logger.warning(f"Chapter {chapter_id} not found")
                continue
            
            # 使用章节逻辑引擎提取规则
            try:
                chapter_rules = self.chapter_engine.extract_chapter_logic(
                    chapter_id=chapter["id"],
                    chapter_title=chapter["title"],
                    chapter_content=chapter["content"],
                    file_type=chapter["file_type"]
                )
                
                # 保存规则到数据库
                for rule in chapter_rules:
                    self.db.execute(
                        """
                        INSERT INTO logic_database
                        (rule_type, source_file_id, source_chapter_id, condition_text, 
                         scoring_logic, importance, confidence, category, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            rule.get("rule_type", "chapter"),
                            chapter["file_id"],
                            chapter_id,
                            rule.get("condition", ""),
                            json.dumps(rule.get("scoring", {})),
                            rule.get("importance", 50),
                            rule.get("confidence", 0.8),
                            rule.get("category", "general"),
                        )
                    )
                
                rules_learned.extend(chapter_rules)
                chapters_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process chapter {chapter_id}: {e}")
                continue
        
        return {
            "rules_learned": len(rules_learned),
            "chapters_processed": chapters_processed,
            "learning_type": "chapter",
            "rules": rules_learned[:10],  # 返回前10条规则作为示例
        }

    def _global_learning(self, task_id: str, file_ids: List[str]) -> Dict[str, Any]:
        """
        全局级学习
        
        分析整个文档的逻辑结构，提取全局规则和模式
        """
        logger.info(f"Global learning: task={task_id}, files={file_ids}")
        
        rules_learned = []
        files_processed = 0  # 初始化计数器
        
        for file_id in file_ids:
            # 更新进度
            progress = int((files_processed / len(file_ids)) * 100)
            task_status = self.cache.get(f"learning_task:{task_id}") or {}
            task_status["progress"] = progress
            task_status["message"] = f"Processing file {files_processed + 1}/{len(file_ids)}..."
            self.cache.set(f"learning_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
            
            # 查询文件信息
            file_info = self.db.query_one(
                "SELECT id, filename, filetype as file_type FROM uploaded_files WHERE id = %s",
                (file_id,)
            )
            
            if not file_info:
                logger.warning(f"File {file_id} not found")
                continue
            
            # 使用全局逻辑引擎提取规则
            try:
                global_rules = self.global_engine.extract_global_logic(
                    file_id=file_id,
                    file_type=file_info["file_type"]
                )
                
                # 保存规则到数据库
                for rule in global_rules:
                    self.db.execute(
                        """
                        INSERT INTO logic_database
                        (rule_type, source_file_id, condition_text, scoring_logic,
                         importance, confidence, category, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            rule.get("rule_type", "global"),
                            file_id,
                            rule.get("condition", ""),
                            json.dumps(rule.get("scoring", {})),
                            rule.get("importance", 50),
                            rule.get("confidence", 0.8),
                            rule.get("category", "general"),
                        )
                    )
                
                rules_learned.extend(global_rules)
                files_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process file {file_id}: {e}")
                continue
        
        return {
            "rules_learned": len(rules_learned),
            "files_processed": files_processed,
            "learning_type": "global",
            "rules": rules_learned[:10],  # 返回前10条规则作为示例
        }

    def get_learning_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询学习任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        task_status = self.cache.get(f"learning_task:{task_id}")
        if not task_status:
            raise ValueError(f"Task {task_id} not found")
        
        return task_status

    def get_learning_result(self, task_id: str) -> Dict[str, Any]:
        """
        获取学习任务完成结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            学习结果
        """
        status = self.get_learning_status(task_id)
        
        if status["status"] != "completed":
            raise ValueError(f"Task {task_id} not completed yet (status: {status['status']})")
        
        return status.get("result", {})

    def get_logic_database(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        获取逻辑数据库统计
        
        Args:
            category: 分类过滤（可选）
            
        Returns:
            统计信息
        """
        try:
            # 查询规则总数
            if category:
                total = self.db.query_one(
                    "SELECT COUNT(*) as count FROM logic_database WHERE category = %s",
                    (category,)
                )["count"]
                
                rules = self.db.query(
                    """
                    SELECT id, rule_type, condition_text, importance, confidence, 
                           category, created_at
                    FROM logic_database
                    WHERE category = %s
                    ORDER BY created_at DESC
                    LIMIT 20
                    """,
                    (category,)
                )
            else:
                total = self.db.query_one(
                    "SELECT COUNT(*) as count FROM logic_database"
                )["count"]
                
                rules = self.db.query(
                    """
                    SELECT id, rule_type, condition_text, importance, confidence,
                           category, created_at
                    FROM logic_database
                    ORDER BY created_at DESC
                    LIMIT 20
                    """
                )
            
            # 统计分类
            category_stats = self.db.query(
                """
                SELECT category, COUNT(*) as count
                FROM logic_database
                GROUP BY category
                ORDER BY count DESC
                """
            )
            
            return {
                "total_rules": total,
                "category_stats": category_stats,
                "recent_rules": rules,
            }
            
        except Exception as e:
            logger.error(f"Get logic database failed: {e}", exc_info=True)
            raise


def main():
    """主入口：接收JSON-RPC风格调用"""
    import sys
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing input file argument"}))
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            request = json.load(f)
        
        method = request.get("method")
        args = request.get("args", {})
        
        service = LogicLearningMCP()
        
        if method == "start_learning":
            result = service.start_learning(**args)
        elif method == "get_learning_status":
            result = service.get_learning_status(**args)
        elif method == "get_learning_result":
            result = service.get_learning_result(**args)
        elif method == "get_logic_database":
            result = service.get_logic_database(**args)
        else:
            result = {"error": f"Unknown method: {method}"}
        
        print(json.dumps({"data": result}))
        
    except Exception as e:
        logger.error(f"Logic learning MCP error: {e}", exc_info=True)
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
