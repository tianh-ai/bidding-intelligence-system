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
        task_id = None
        
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
                "status": "completed",
                "progress": 100,
                "message": "Learning completed successfully",
                "result": result,
            }
            
        except Exception as e:
            logger.error(f"Start learning failed: {e}", exc_info=True)
            if task_id:
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
            progress = int((chapters_processed / len(chapter_ids)) * 100) if chapter_ids else 0
            task_status = self.cache.get(f"learning_task:{task_id}") or {}
            task_status["progress"] = progress
            task_status["message"] = f"Processing chapter {chapters_processed + 1}/{len(chapter_ids)}..."
            self.cache.set(f"learning_task:{task_id}", task_status, ttl=TASK_STATUS_TTL)
            
            # 查询章节信息
            chapter = self.db.query_one(
                """
                SELECT c.id, c.file_id, c.chapter_number, c.chapter_title as title, 
                       c.content, c.chapter_level as level, c.position_order as order_index,
                       f.filename, f.filetype as file_type
                FROM chapters c
                JOIN uploaded_files f ON c.file_id = f.id
                WHERE c.id = %s
                """,
                (chapter_id,)
            )
            
            if not chapter:
                logger.warning(f"Chapter {chapter_id} not found")
                continue
            
            # 使用章节逻辑引擎学习章节（调用真实 learn_chapter 方法）
            try:
                # 构建章节对象
                tender_chapter = {
                    'id': chapter['id'],
                    'chapter_title': chapter.get('title', ''),
                    'content': chapter.get('content', ''),
                    'level': chapter.get('level', 1),
                    'order_index': chapter.get('order_index', 0)
                }
                
                # 由于单文件学习，proposal_chapter 与 tender_chapter 相同
                proposal_chapter = tender_chapter
                
                # 调用真实学习方法
                chapter_package = self.chapter_engine.learn_chapter(
                    tender_chapter=tender_chapter,
                    proposal_chapter=proposal_chapter,
                    boq=None,
                    custom_rules=None
                )
                
                # 收集学习到的规则
                for rule_type in ['structure_rules', 'content_rules', 'mandatory_rules', 'scoring_rules']:
                    rules = chapter_package.get(rule_type, [])
                    if rules:
                        for rule in rules:
                            rule['source'] = 'chapter_learning'
                            rules_learned.append(rule)
                
                logger.info(f"Chapter {chapter_id} learning completed: {len(chapter_package.get('structure_rules', []))} structure rules, "
                           f"{len(chapter_package.get('mandatory_rules', []))} mandatory rules, "
                           f"{len(chapter_package.get('scoring_rules', []))} scoring rules")
                chapters_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process chapter {chapter_id}: {e}", exc_info=True)
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
        files_processed = 0
        
        for file_id in file_ids:
            # 更新进度
            progress = int((files_processed / len(file_ids)) * 100) if file_ids else 0
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
            
            # 查询文件所有章节
            chapters = self.db.query(
                """
                SELECT id, file_id, chapter_number, chapter_title as title, 
                       content, chapter_level as level, position_order as order_index
                FROM chapters
                WHERE file_id = %s
                ORDER BY position_order ASC
                """,
                (file_id,)
            )
            
            if not chapters:
                logger.warning(f"No chapters found for file {file_id}")
                files_processed += 1
                continue
            
            # 使用全局逻辑引擎学习（调用真实 learn_global 方法）
            try:
                # 构建文件对象
                tender_doc = {
                    'id': file_info['id'],
                    'filename': file_info['filename'],
                    'file_type': file_info['file_type'],
                    'chapters': chapters
                }
                
                # 由于单文件学习，proposal_doc 与 tender_doc 相同
                proposal_doc = tender_doc
                
                # 构建章节逻辑包
                chapter_packages = []
                for chapter in chapters:
                    chapter_package = {
                        'chapter_id': chapter['id'],
                        'title': chapter['title'],
                        'level': chapter['level']
                    }
                    chapter_packages.append(chapter_package)
                
                # 调用真实学习方法
                global_package = self.global_engine.learn_global(
                    tender_doc=tender_doc,
                    proposal_doc=proposal_doc,
                    chapter_packages=chapter_packages
                )
                
                # 收集学习到的规则
                for rule_type in ['structure_rules', 'content_rules', 'consistency_rules', 'scoring_rules']:
                    rules = global_package.get(rule_type, [])
                    if rules:
                        for rule in rules:
                            rule['source'] = 'global_learning'
                            rules_learned.append(rule)
                
                logger.info(f"File {file_id} global learning completed: "
                           f"{len(global_package.get('structure_rules', []))} structure rules, "
                           f"{len(global_package.get('consistency_rules', []))} consistency rules")
                files_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process file {file_id}: {e}", exc_info=True)
                continue
        
        return {
            "rules_learned": len(rules_learned),
            "files_processed": files_processed,
            "learning_type": "global",
            "rules": rules_learned[:20],  # 返回前20条规则作为示例
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
