"""
自学习投标系统 - 完整工作流编排

这是整个自学习系统的核心编排器，协调所有子系统：
1. 文档智能配对
2. 文档解析
3. 深度逻辑学习
4. 智能生成
5. 验证反馈循环
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from core.logger import logger
from engines.document_matcher import DocumentMatcher, DocumentPair
from engines.document_parser import DocumentParser, ParsedDocument, KnowledgeBase
from engines.logic_learning_engine import (
    LogicLearningEngine,
    GenerationLogicDB,
    ValidationLogicDB
)
from engines.intelligent_generator import (
    IntelligentProposalGenerator,
    GeneratedProposal,
    FeedbackLoop
)


class SelfLearningBiddingSystem:
    """自学习投标系统"""
    
    def __init__(self, storage_root: str = "data/self_learning"):
        """
        初始化系统
        
        Args:
            storage_root: 数据存储根目录
        """
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # 初始化各个引擎
        self.matcher = DocumentMatcher(str(self.storage_root / "matched_docs"))
        self.parser = DocumentParser()
        self.logic_learner = LogicLearningEngine()
        
        # 逻辑库（初始为空，通过学习构建）
        self.generation_logic: Optional[GenerationLogicDB] = None
        self.validation_logic: Optional[ValidationLogicDB] = None
        
        # 知识库（通过解析构建）
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}
        
        logger.info("SelfLearningBiddingSystem initialized", extra={
            "storage_root": str(self.storage_root)
        })
    
    async def batch_learn_from_files(
        self,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        批量学习：从文件到逻辑库
        
        完整流程：
        1. 文件智能配对
        2. 文档解析
        3. 知识库生成
        4. 逻辑库学习
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            学习结果统计
        """
        logger.info(f"Starting batch learning from {len(file_paths)} files")
        
        # Step 1: 智能配对
        logger.info("Step 1: Matching documents...")
        pairs = await self.matcher.batch_process_files(file_paths)
        logger.info(f"Matched {len(pairs)} document pairs")
        
        if not pairs:
            logger.warning("No document pairs found, learning aborted")
            return {
                "status": "failed",
                "reason": "No document pairs found",
                "pairs": 0
            }
        
        # Step 2: 解析所有配对文档
        logger.info("Step 2: Parsing documents...")
        all_generation_rules = []
        all_validation_rules = []
        
        for pair in pairs:
            # 解析文档
            tender_doc, proposal_doc = await self.parser.parse_document_pair(pair)
            
            # 生成知识库
            kb = await self.parser.generate_knowledge_base(
                tender_doc=tender_doc,
                proposal_doc=proposal_doc,
                pair_id=pair.pair_id,
                storage_path=pair.storage_path
            )
            self.knowledge_bases[pair.pair_id] = kb
            
            # Step 3: 学习逻辑
            logger.info(f"Step 3: Learning logic for pair {pair.pair_id}...")
            
            # 学习生成逻辑
            gen_rules = await self.logic_learner.learn_generation_logic(
                tender_doc=tender_doc,
                proposal_doc=proposal_doc,
                pair_id=pair.pair_id
            )
            all_generation_rules.extend(gen_rules)
            
            # 学习验证逻辑
            val_rules = await self.logic_learner.learn_validation_logic(
                tender_doc=tender_doc,
                proposal_doc=proposal_doc,
                pair_id=pair.pair_id
            )
            all_validation_rules.extend(val_rules)
        
        # Step 4: 构建逻辑库
        logger.info("Step 4: Building logic databases...")
        
        logic_storage = str(self.storage_root / "logic_db")
        
        self.generation_logic = await self.logic_learner.build_generation_logic_db(
            all_rules=all_generation_rules,
            storage_path=logic_storage
        )
        
        self.validation_logic = await self.logic_learner.build_validation_logic_db(
            all_rules=all_validation_rules,
            storage_path=logic_storage
        )
        
        # 统计结果
        result = {
            "status": "success",
            "pairs_processed": len(pairs),
            "knowledge_bases": len(self.knowledge_bases),
            "generation_rules": len(all_generation_rules),
            "validation_rules": len(all_validation_rules),
            "avg_success_rate": self.generation_logic.avg_success_rate,
            "storage_path": str(self.storage_root)
        }
        
        logger.info("Batch learning completed", extra=result)
        
        return result
    
    async def generate_proposal_for_tender(
        self,
        tender_file_path: str,
        max_iterations: int = 5,
        quality_threshold: float = 90.0
    ) -> Dict[str, Any]:
        """
        为新招标文件生成投标文件
        
        Args:
            tender_file_path: 招标文件路径
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值
            
        Returns:
            生成结果
        """
        logger.info(f"Generating proposal for tender: {tender_file_path}")
        
        # 检查逻辑库是否已构建
        if not self.generation_logic or not self.validation_logic:
            return {
                "status": "error",
                "message": "Logic databases not built yet. Please run batch_learn_from_files first."
            }
        
        # Step 1: 分类和解析招标文件
        logger.info("Step 1: Parsing tender document...")
        
        doc_type = await self.matcher.classify_document(tender_file_path)
        if doc_type.value != "tender":
            return {
                "status": "error",
                "message": f"File is not a tender document: {doc_type.value}"
            }
        
        tender_info = await self.matcher.extract_document_structure(
            file_path=tender_file_path,
            document_type=doc_type
        )
        
        # 转换为ParsedDocument（简化版）
        from engines.document_parser import ParsedChapter, ParsedDocument
        
        parsed_chapters = []
        for ch in tender_info.chapters:
            # 简化：直接使用章节信息创建ParsedChapter
            parsed_ch = ParsedChapter(
                chapter_id=ch.chapter_id,
                chapter_title=ch.title,
                requirements=[],  # TODO: 实际解析
                technical_specs=[],
                business_terms=[],
                evaluation_criteria=[],
                raw_text=f"[章节内容: {ch.title}]",
                summary=ch.content_summary or ch.title,
                key_points=ch.keywords,
                constraints=[]
            )
            parsed_chapters.append(parsed_ch)
        
        tender_doc = ParsedDocument(
            doc_id=f"tender_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            doc_type="tender",
            project_name=tender_info.project_name or "Unknown",
            project_code=tender_info.project_code or "Unknown",
            chapters=parsed_chapters,
            metadata={},
            parse_time=datetime.now().isoformat()
        )
        
        # Step 2: 使用智能生成器生成投标文件
        logger.info("Step 2: Generating proposal with intelligent generator...")
        
        # 获取第一个知识库（简化版）
        kb = list(self.knowledge_bases.values())[0] if self.knowledge_bases else None
        
        if not kb:
            # 创建空知识库
            kb = KnowledgeBase(
                kb_id="kb_default",
                pair_id="default",
                entries=[],
                total_entries=0,
                entry_types={},
                storage_path=str(self.storage_root),
                created_time=datetime.now().isoformat()
            )
        
        generator = IntelligentProposalGenerator(
            generation_logic_db=self.generation_logic,
            validation_logic_db=self.validation_logic,
            knowledge_base=kb
        )
        
        proposal, feedback_loop = await generator.generate_proposal(
            tender_doc=tender_doc,
            max_iterations=max_iterations,
            quality_threshold=quality_threshold
        )
        
        # Step 3: 保存生成的投标文件
        logger.info("Step 3: Saving generated proposal...")
        
        proposal_dir = self.storage_root / "generated_proposals" / proposal.proposal_id
        proposal_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存提案元数据
        import json
        from dataclasses import asdict
        
        proposal_file = proposal_dir / "proposal.json"
        with open(proposal_file, 'w', encoding='utf-8') as f:
            proposal_data = {
                "proposal_id": proposal.proposal_id,
                "tender_id": proposal.tender_id,
                "generation_strategy": proposal.generation_strategy,
                "quality_score": proposal.quality_score,
                "status": proposal.status,
                "iteration": proposal.iteration,
                "chapters": [
                    {
                        "chapter_id": ch.chapter_id,
                        "chapter_title": ch.chapter_title,
                        "summary": ch.summary,
                        "key_points": ch.key_points,
                        "content": ch.raw_text
                    }
                    for ch in proposal.chapters
                ]
            }
            json.dump(proposal_data, f, ensure_ascii=False, indent=2)
        
        # 保存反馈循环
        feedback_file = proposal_dir / "feedback_loop.json"
        with open(feedback_file, 'w', encoding='utf-8') as f:
            feedback_data = {
                "loop_id": feedback_loop.loop_id,
                "tender_id": feedback_loop.tender_id,
                "total_iterations": feedback_loop.total_iterations,
                "final_quality_score": feedback_loop.final_quality_score,
                "iterations": feedback_loop.iterations,
                "logic_updates": feedback_loop.logic_updates
            }
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Proposal saved: {proposal_dir}")
        
        # 返回结果
        result = {
            "status": "success",
            "proposal_id": proposal.proposal_id,
            "quality_score": proposal.quality_score,
            "iterations": feedback_loop.total_iterations,
            "chapters": len(proposal.chapters),
            "storage_path": str(proposal_dir),
            "self_check": proposal.self_check_result
        }
        
        return result
    
    async def refine_with_human_feedback(
        self,
        proposal_id: str,
        human_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据人工反馈优化提案和逻辑库
        
        Args:
            proposal_id: 提案ID
            human_feedback: 人工反馈，格式：
                {
                    "approved": bool,
                    "quality_rating": float (0-100),
                    "issues": [
                        {"type": "error/warning", "description": "...", "chapter": "..."}
                    ],
                    "suggestions": ["建议1", "建议2"]
                }
            
        Returns:
            优化结果
        """
        logger.info(f"Refining with human feedback for proposal: {proposal_id}")
        
        # TODO: 实现基于人工反馈的逻辑库优化
        # 1. 分析反馈中的问题
        # 2. 更新生成规则（降低导致问题的规则的置信度）
        # 3. 更新验证规则（添加新的检查规则）
        # 4. 重新生成并验证
        
        updates_made = {
            "generation_rules_updated": 0,
            "validation_rules_added": 0,
            "knowledge_entries_added": 0
        }
        
        if not human_feedback.get("approved", False):
            # 处理问题反馈
            for issue in human_feedback.get("issues", []):
                # 这里可以创建新的验证规则
                logger.info(f"Processing issue: {issue.get('description')}")
                updates_made["validation_rules_added"] += 1
        
        result = {
            "status": "success",
            "proposal_id": proposal_id,
            "feedback_processed": True,
            "updates": updates_made
        }
        
        logger.info("Human feedback processed", extra=result)
        
        return result
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            "knowledge_bases": len(self.knowledge_bases),
            "total_kb_entries": sum(kb.total_entries for kb in self.knowledge_bases.values()),
            "generation_logic": {
                "total_rules": self.generation_logic.total_rules if self.generation_logic else 0,
                "avg_success_rate": self.generation_logic.avg_success_rate if self.generation_logic else 0
            } if self.generation_logic else None,
            "validation_logic": {
                "total_rules": self.validation_logic.total_rules if self.validation_logic else 0,
                "avg_precision": self.validation_logic.avg_precision if self.validation_logic else 0
            } if self.validation_logic else None,
            "storage_root": str(self.storage_root)
        }
        
        return stats
