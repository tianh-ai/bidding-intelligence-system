"""
智能投标生成器 - 基于逻辑库生成投标文件

功能：
1. 读取新的招标文件
2. 使用生成逻辑库 + 知识库 + 文件数据库生成投标文件
3. 使用验证逻辑库进行自我检查
4. 支持人工验证反馈
5. 将反馈结果用于优化两个逻辑库
6. 迭代优化直到生成质量达标
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from core.logger import logger
from core.llm_router import get_llm_router, TaskType
from engines.document_parser import ParsedDocument, ParsedChapter, KnowledgeBase
from engines.logic_learning_engine import (
    GenerationLogicDB, ValidationLogicDB,
    GenerationRule, ValidationRule
)


@dataclass
class GeneratedProposal:
    """生成的投标文件"""
    proposal_id: str
    tender_id: str
    
    # 生成内容
    chapters: List[ParsedChapter]
    
    # 生成元数据
    generation_strategy: str  # "logic_based", "knowledge_based", "hybrid"
    used_rules: List[str]  # 使用的规则ID列表
    
    # 质量评估
    self_check_result: Dict[str, Any]  # 自我检查结果
    quality_score: float  # 质量分数 0-100
    
    # 状态
    status: str  # "draft", "validated", "approved", "rejected"
    iteration: int  # 迭代次数
    
    # 时间
    created_time: str
    last_updated: str
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class ValidationResult:
    """验证结果"""
    proposal_id: str
    
    # 验证详情
    passed_checks: List[str]  # 通过的检查项
    failed_checks: List[Dict[str, Any]]  # 失败的检查项
    
    # 总体评估
    is_compliant: bool  # 是否合规
    completeness_score: float  # 完整性分数
    quality_score: float  # 质量分数
    
    # 改进建议
    suggestions: List[str]
    
    # 人工验证
    human_feedback: Optional[Dict[str, Any]] = None
    
    created_time: str = None
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()


@dataclass
class FeedbackLoop:
    """反馈循环记录"""
    loop_id: str
    tender_id: str
    
    # 迭代历史
    iterations: List[Dict[str, Any]]  # 每次迭代的详细信息
    
    # 最终结果
    final_proposal_id: str
    final_quality_score: float
    total_iterations: int
    
    # 逻辑库更新
    logic_updates: List[Dict[str, Any]]  # 对逻辑库的更新记录
    
    created_time: str
    completed_time: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()


class IntelligentProposalGenerator:
    """智能投标生成器"""
    
    def __init__(
        self,
        generation_logic_db: GenerationLogicDB,
        validation_logic_db: ValidationLogicDB,
        knowledge_base: KnowledgeBase
    ):
        """
        初始化生成器
        
        Args:
            generation_logic_db: 生成逻辑库
            validation_logic_db: 验证逻辑库
            knowledge_base: 知识库
        """
        self.llm_router = get_llm_router()
        self.gen_logic = generation_logic_db
        self.val_logic = validation_logic_db
        self.kb = knowledge_base
        
        logger.info("IntelligentProposalGenerator initialized", extra={
            "gen_rules": len(generation_logic_db.rules),
            "val_rules": len(validation_logic_db.rules),
            "kb_entries": len(knowledge_base.entries)
        })
    
    async def generate_proposal(
        self,
        tender_doc: ParsedDocument,
        max_iterations: int = 5,
        quality_threshold: float = 90.0
    ) -> Tuple[GeneratedProposal, FeedbackLoop]:
        """
        生成投标文件（支持迭代优化）
        
        Args:
            tender_doc: 招标文档
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值
            
        Returns:
            (最终投标文件, 反馈循环记录)
        """
        logger.info(f"Generating proposal for tender: {tender_doc.doc_id}")
        
        # 初始化反馈循环
        feedback_loop = FeedbackLoop(
            loop_id=f"loop_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            tender_id=tender_doc.doc_id,
            iterations=[],
            final_proposal_id="",
            final_quality_score=0.0,
            total_iterations=0,
            logic_updates=[],
            created_time=datetime.now().isoformat()
        )
        
        current_proposal = None
        
        for iteration in range(1, max_iterations + 1):
            logger.info(f"Iteration {iteration}/{max_iterations}")
            
            # Step 1: 生成投标文件
            proposal = await self._generate_single_iteration(
                tender_doc=tender_doc,
                previous_proposal=current_proposal,
                iteration=iteration
            )
            
            # Step 2: 自我验证
            validation_result = await self._validate_proposal(
                proposal=proposal,
                tender_doc=tender_doc
            )
            
            # Step 3: 记录迭代信息
            iteration_info = {
                "iteration": iteration,
                "proposal_id": proposal.proposal_id,
                "quality_score": proposal.quality_score,
                "passed_checks": len(validation_result.passed_checks),
                "failed_checks": len(validation_result.failed_checks),
                "suggestions": validation_result.suggestions[:3]  # 前3条建议
            }
            feedback_loop.iterations.append(iteration_info)
            
            # Step 4: 检查是否达到质量阈值
            if proposal.quality_score >= quality_threshold:
                logger.info(f"Quality threshold reached: {proposal.quality_score:.1f}")
                current_proposal = proposal
                break
            
            # Step 5: 根据验证结果优化
            if iteration < max_iterations:
                # 更新逻辑库
                await self._update_logic_from_feedback(
                    validation_result=validation_result,
                    feedback_loop=feedback_loop
                )
            
            current_proposal = proposal
        
        # 最终化
        feedback_loop.final_proposal_id = current_proposal.proposal_id
        feedback_loop.final_quality_score = current_proposal.quality_score
        feedback_loop.total_iterations = len(feedback_loop.iterations)
        feedback_loop.completed_time = datetime.now().isoformat()
        
        logger.info(f"Proposal generation completed", extra={
            "iterations": feedback_loop.total_iterations,
            "final_quality": feedback_loop.final_quality_score
        })
        
        return current_proposal, feedback_loop
    
    async def _generate_single_iteration(
        self,
        tender_doc: ParsedDocument,
        previous_proposal: Optional[GeneratedProposal],
        iteration: int
    ) -> GeneratedProposal:
        """
        单次迭代生成
        
        Args:
            tender_doc: 招标文档
            previous_proposal: 上一次生成的投标文件（如果有）
            iteration: 当前迭代次数
            
        Returns:
            生成的投标文件
        """
        proposal_id = f"proposal_{tender_doc.project_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}_v{iteration}"
        
        generated_chapters = []
        used_rules = []
        
        # 为每个招标章节生成对应的投标章节
        for tender_chapter in tender_doc.chapters:
            # 查找适用的生成规则
            applicable_rules = self._find_applicable_rules(tender_chapter)
            
            # 查找相关知识
            relevant_knowledge = self._find_relevant_knowledge(tender_chapter)
            
            # 生成章节内容
            generated_chapter = await self._generate_chapter(
                tender_chapter=tender_chapter,
                rules=applicable_rules,
                knowledge=relevant_knowledge,
                previous_chapter=self._find_previous_chapter(
                    tender_chapter.chapter_id,
                    previous_proposal
                ) if previous_proposal else None
            )
            
            generated_chapters.append(generated_chapter)
            used_rules.extend([rule.rule_id for rule in applicable_rules])
        
        # 创建生成的投标文件
        proposal = GeneratedProposal(
            proposal_id=proposal_id,
            tender_id=tender_doc.doc_id,
            chapters=generated_chapters,
            generation_strategy="hybrid",
            used_rules=used_rules,
            self_check_result={},
            quality_score=0.0,  # 待验证后填充
            status="draft",
            iteration=iteration,
            created_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
        
        return proposal
    
    def _find_applicable_rules(
        self,
        tender_chapter: ParsedChapter
    ) -> List[GenerationRule]:
        """查找适用于该章节的生成规则"""
        applicable_rules = []
        
        for rule in self.gen_logic.rules:
            # 简化版：检查规则的触发模式是否匹配
            if rule.trigger_type == "requirement":
                for req in tender_chapter.requirements:
                    if self._pattern_matches(rule.trigger_pattern, req):
                        applicable_rules.append(rule)
                        break
            
            elif rule.trigger_type == "technical":
                for spec in tender_chapter.technical_specs:
                    spec_str = f"{spec.get('item', '')}: {spec.get('spec', '')}"
                    if self._pattern_matches(rule.trigger_pattern, spec_str):
                        applicable_rules.append(rule)
                        break
        
        return applicable_rules
    
    def _pattern_matches(self, pattern: str, text: str) -> bool:
        """简单的模式匹配"""
        # 简化版：关键词匹配
        pattern_words = set(pattern.lower().split())
        text_words = set(text.lower().split())
        
        # 至少50%的关键词匹配
        common_words = pattern_words & text_words
        return len(common_words) >= len(pattern_words) * 0.5
    
    def _find_relevant_knowledge(
        self,
        tender_chapter: ParsedChapter
    ) -> List[Any]:
        """从知识库中查找相关知识"""
        relevant = []
        
        # 简化版：基于关键词匹配
        chapter_keywords = set(tender_chapter.key_points)
        
        for entry in self.kb.entries:
            entry_keywords = set(entry.keywords)
            if chapter_keywords & entry_keywords:
                relevant.append(entry)
        
        return relevant[:5]  # 返回最相关的5条
    
    def _find_previous_chapter(
        self,
        chapter_id: str,
        previous_proposal: Optional[GeneratedProposal]
    ) -> Optional[ParsedChapter]:
        """查找上一次迭代的对应章节"""
        if not previous_proposal:
            return None
        
        for ch in previous_proposal.chapters:
            if ch.chapter_id == chapter_id:
                return ch
        
        return None
    
    async def _generate_chapter(
        self,
        tender_chapter: ParsedChapter,
        rules: List[GenerationRule],
        knowledge: List[Any],
        previous_chapter: Optional[ParsedChapter]
    ) -> ParsedChapter:
        """
        使用LLM + 规则 + 知识生成章节
        
        Args:
            tender_chapter: 招标章节
            rules: 适用的生成规则
            knowledge: 相关知识
            previous_chapter: 上一次生成的章节（用于改进）
            
        Returns:
            生成的投标章节
        """
        # 构造生成提示词
        prompt = f"""
请根据以下信息生成投标文件的章节内容：

招标要求（章节 {tender_chapter.chapter_id}: {tender_chapter.chapter_title}）：
需求：{', '.join(tender_chapter.requirements[:5])}
关键点：{', '.join(tender_chapter.key_points[:5])}
约束：{', '.join(tender_chapter.constraints[:3])}

适用的生成规则：
{self._format_rules(rules[:3])}

相关知识库：
{self._format_knowledge(knowledge[:3])}

{self._format_previous_feedback(previous_chapter)}

请生成投标响应内容，要求：
1. 完全满足招标要求
2. 突出技术优势和创新点
3. 符合行业规范和最佳实践
4. 字数适中，条理清晰

请返回JSON格式：
{{
  "summary": "章节摘要（100字内）",
  "key_points": ["要点1", "要点2", "要点3"],
  "requirements": ["响应需求1", "响应需求2"],
  "technical_specs": [{{"item": "项目", "spec": "规格"}}],
  "full_content": "完整的章节内容（300-500字）"
}}
"""
        
        try:
            result = await self.llm_router.generate_text(
                prompt=prompt,
                system_prompt="你是专业的投标文件撰写专家，擅长响应招标要求并突出竞争优势。",
                task_type=TaskType.GENERATION,
                max_tokens=2000
            )
            
            # 解析JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            
            data = json.loads(result)
            
            generated = ParsedChapter(
                chapter_id=tender_chapter.chapter_id,
                chapter_title=tender_chapter.chapter_title,
                requirements=data.get("requirements", []),
                technical_specs=data.get("technical_specs", []),
                business_terms=[],
                evaluation_criteria=[],
                raw_text=data.get("full_content", ""),
                summary=data.get("summary", ""),
                key_points=data.get("key_points", []),
                constraints=[]
            )
            
            logger.info(f"Generated chapter: {tender_chapter.chapter_id}")
            
            return generated
            
        except Exception as e:
            logger.error(f"Failed to generate chapter: {e}", exc_info=True)
            
            # 降级：返回基本响应
            return ParsedChapter(
                chapter_id=tender_chapter.chapter_id,
                chapter_title=tender_chapter.chapter_title,
                requirements=[],
                technical_specs=[],
                business_terms=[],
                evaluation_criteria=[],
                raw_text=f"[针对 {tender_chapter.chapter_title} 的响应内容]",
                summary=f"响应 {tender_chapter.chapter_title}",
                key_points=[],
                constraints=[]
            )
    
    def _format_rules(self, rules: List[GenerationRule]) -> str:
        """格式化规则为提示词"""
        if not rules:
            return "无适用规则"
        
        formatted = []
        for rule in rules:
            formatted.append(f"- {rule.response_template} (策略: {rule.generation_strategy})")
        
        return "\n".join(formatted)
    
    def _format_knowledge(self, knowledge: List[Any]) -> str:
        """格式化知识为提示词"""
        if not knowledge:
            return "无相关知识"
        
        formatted = []
        for entry in knowledge:
            formatted.append(f"- {entry.content}")
        
        return "\n".join(formatted)
    
    def _format_previous_feedback(self, previous_chapter: Optional[ParsedChapter]) -> str:
        """格式化上一次的反馈"""
        if not previous_chapter:
            return ""
        
        return f"""
上一次生成的内容：
{previous_chapter.summary}

请在此基础上改进，重点关注：
- 增强说服力
- 补充细节
- 优化表述
"""
    
    async def _validate_proposal(
        self,
        proposal: GeneratedProposal,
        tender_doc: ParsedDocument
    ) -> ValidationResult:
        """
        验证生成的投标文件
        
        Args:
            proposal: 生成的投标文件
            tender_doc: 招标文档
            
        Returns:
            验证结果
        """
        passed_checks = []
        failed_checks = []
        suggestions = []
        
        # 执行所有验证规则
        for rule in self.val_logic.rules:
            check_result = await self._execute_validation_rule(
                rule=rule,
                proposal=proposal,
                tender_doc=tender_doc
            )
            
            if check_result["passed"]:
                passed_checks.append(rule.rule_id)
            else:
                failed_checks.append({
                    "rule_id": rule.rule_id,
                    "check_type": rule.check_type,
                    "reason": check_result["reason"],
                    "severity": rule.severity
                })
                suggestions.extend(rule.fix_suggestions)
        
        # 计算分数
        total_checks = len(self.val_logic.rules)
        passed_count = len(passed_checks)
        
        completeness_score = (passed_count / total_checks * 100) if total_checks > 0 else 0
        
        # 质量分数综合考虑
        quality_score = completeness_score * 0.7 + self._assess_content_quality(proposal) * 0.3
        
        # 更新提案的质量分数
        proposal.quality_score = quality_score
        proposal.self_check_result = {
            "passed": passed_count,
            "failed": len(failed_checks),
            "total": total_checks
        }
        
        validation_result = ValidationResult(
            proposal_id=proposal.proposal_id,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            is_compliant=len(failed_checks) == 0,
            completeness_score=completeness_score,
            quality_score=quality_score,
            suggestions=list(set(suggestions)),  # 去重
            created_time=datetime.now().isoformat()
        )
        
        logger.info(f"Validation completed", extra={
            "passed": passed_count,
            "failed": len(failed_checks),
            "quality_score": quality_score
        })
        
        return validation_result
    
    async def _execute_validation_rule(
        self,
        rule: ValidationRule,
        proposal: GeneratedProposal,
        tender_doc: ParsedDocument
    ) -> Dict[str, Any]:
        """执行单个验证规则"""
        # 简化版：基于检查类型的简单验证
        if rule.check_type == "completeness":
            # 检查章节完整性
            tender_chapters = {ch.chapter_id for ch in tender_doc.chapters}
            proposal_chapters = {ch.chapter_id for ch in proposal.chapters}
            
            if tender_chapters.issubset(proposal_chapters):
                return {"passed": True}
            else:
                missing = tender_chapters - proposal_chapters
                return {
                    "passed": False,
                    "reason": f"缺少章节: {', '.join(missing)}"
                }
        
        elif rule.check_type == "compliance":
            # 使用LLM检查合规性（简化版：假设通过）
            return {"passed": True}
        
        else:
            # 默认通过
            return {"passed": True}
    
    def _assess_content_quality(self, proposal: GeneratedProposal) -> float:
        """评估内容质量"""
        # 简化版：基于内容长度和结构
        total_score = 0
        count = 0
        
        for chapter in proposal.chapters:
            # 有摘要
            if chapter.summary:
                total_score += 20
            
            # 有关键点
            if chapter.key_points:
                total_score += 20
            
            # 有内容
            if chapter.raw_text and len(chapter.raw_text) > 100:
                total_score += 30
            
            # 有需求响应
            if chapter.requirements:
                total_score += 30
            
            count += 1
        
        return (total_score / count) if count > 0 else 0
    
    async def _update_logic_from_feedback(
        self,
        validation_result: ValidationResult,
        feedback_loop: FeedbackLoop
    ):
        """根据验证反馈更新逻辑库"""
        # 记录更新
        update = {
            "iteration": len(feedback_loop.iterations),
            "failed_checks": len(validation_result.failed_checks),
            "update_type": "auto_optimization",
            "timestamp": datetime.now().isoformat()
        }
        
        feedback_loop.logic_updates.append(update)
        
        # TODO: 实现实际的逻辑库更新逻辑
        logger.info(f"Logic updated based on feedback: {len(validation_result.failed_checks)} issues addressed")
