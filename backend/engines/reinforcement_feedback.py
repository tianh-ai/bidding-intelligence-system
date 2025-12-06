"""
强化学习反馈机制 (Reinforcement Learning Feedback)
错误库管理、反馈循环、模型优化
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timedelta
from core.logger import logger
from core.llm_router import get_llm_router, TaskType


class FeedbackType(str, Enum):
    """反馈类型"""
    POSITIVE = "positive"  # 正面反馈
    NEGATIVE = "negative"  # 负面反馈
    CORRECTIVE = "corrective"  # 纠正反馈
    QUALITY_IMPROVEMENT = "quality_improvement"  # 质量改进


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    CRITICAL = "critical"  # 致命错误
    MAJOR = "major"  # 主要错误
    MINOR = "minor"  # 轻微错误
    INFO = "info"  # 信息提示


class ErrorRecord(BaseModel):
    """错误记录"""
    error_id: str = Field(..., description="错误ID")
    proposal_id: str = Field(..., description="投标书ID")
    error_type: str = Field(..., description="错误类型")
    severity: ErrorSeverity = Field(..., description="严重程度")
    description: str = Field(..., description="错误描述")
    location: str = Field(..., description="错误位置")
    correction: Optional[str] = Field(None, description="纠正方案")
    occurrence_count: int = Field(default=1, description="出现次数")
    first_occurred: datetime = Field(default_factory=datetime.now)
    last_occurred: datetime = Field(default_factory=datetime.now)
    fixed: bool = Field(default=False, description="是否已修复")


class FeedbackRecord(BaseModel):
    """反馈记录"""
    feedback_id: str = Field(..., description="反馈ID")
    proposal_id: str = Field(..., description="投标书ID")
    feedback_type: FeedbackType = Field(..., description="反馈类型")
    score: float = Field(..., ge=0, le=100, description="评分 0-100")
    content: str = Field(..., description="反馈内容")
    source: str = Field(..., description="反馈来源：SYSTEM/USER/EVALUATOR")
    created_at: datetime = Field(default_factory=datetime.now)
    addressed: bool = Field(default=False, description="是否已处理")


class PatternAnalysis(BaseModel):
    """模式分析"""
    pattern_id: str = Field(..., description="模式ID")
    error_type: str = Field(..., description="错误类型")
    frequency: int = Field(..., description="出现频率")
    affected_proposals: List[str] = Field(..., description="受影响的投标书")
    root_cause: Optional[str] = Field(None, description="根本原因")
    prevention_strategy: Optional[str] = Field(None, description="预防策略")
    effectiveness_score: Optional[float] = Field(None, description="有效性评分")


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    suggestion_id: str = Field(..., description="建议ID")
    category: str = Field(..., description="类别：GENERATION/SCORING/COMPARISON")
    priority: str = Field(..., description="优先级：HIGH/MEDIUM/LOW")
    description: str = Field(..., description="建议描述")
    expected_impact: Dict = Field(..., description="预期影响")
    implementation_cost: str = Field(..., description="实施成本：LOW/MEDIUM/HIGH")
    confidence: float = Field(..., ge=0, le=100, description="建议可信度")


class ReinforcementLearningFeedback:
    """
    强化学习反馈机制
    
    功能：
    - 错误库管理（收集、分类、追踪）
    - 反馈循环（用户反馈、系统反馈）
    - 模式识别（错误模式、成功模式）
    - 模型优化（基于反馈自动优化）
    """
    
    def __init__(self):
        """初始化反馈机制"""
        logger.info("ReinforcementLearningFeedback initialized")
        self.error_records: List[ErrorRecord] = []
        self.feedback_records: List[FeedbackRecord] = []
        self.pattern_history: List[PatternAnalysis] = []
        self.optimization_suggestions: List[OptimizationSuggestion] = []
        self.llm_router = get_llm_router()  # 获取LLM路由器
        logger.info("LLM Router integrated into ReinforcementLearningFeedback")
    
    async def record_error(
        self,
        proposal_id: str,
        error_type: str,
        severity: ErrorSeverity,
        description: str,
        location: str,
        correction: Optional[str] = None
    ) -> ErrorRecord:
        """
        记录错误
        
        Args:
            proposal_id: 投标书ID
            error_type: 错误类型
            severity: 严重程度
            description: 错误描述
            location: 错误位置
            correction: 纠正方案
            
        Returns:
            错误记录
        """
        error_id = f"err_{proposal_id}_{datetime.now().timestamp()}"
        
        # 检查是否是重复错误
        existing_error = next(
            (e for e in self.error_records
             if e.error_type == error_type and e.proposal_id == proposal_id),
            None
        )
        
        if existing_error and not existing_error.fixed:
            # 更新现有错误记录
            existing_error.occurrence_count += 1
            existing_error.last_occurred = datetime.now()
            logger.info(
                f"Error recorded (duplicate)",
                extra={
                    "error_type": error_type,
                    "occurrence_count": existing_error.occurrence_count
                }
            )
            return existing_error
        
        # 创建新错误记录
        error = ErrorRecord(
            error_id=error_id,
            proposal_id=proposal_id,
            error_type=error_type,
            severity=severity,
            description=description,
            location=location,
            correction=correction
        )
        
        self.error_records.append(error)
        
        logger.info(
            f"Error recorded",
            extra={
                "error_id": error_id,
                "error_type": error_type,
                "severity": severity.value
            }
        )
        
        return error
    
    async def submit_feedback(
        self,
        proposal_id: str,
        feedback_type: FeedbackType,
        score: float,
        content: str,
        source: str = "USER"
    ) -> FeedbackRecord:
        """
        提交反馈
        
        Args:
            proposal_id: 投标书ID
            feedback_type: 反馈类型
            score: 评分 0-100
            content: 反馈内容
            source: 反馈来源
            
        Returns:
            反馈记录
        """
        feedback_id = f"fb_{proposal_id}_{datetime.now().timestamp()}"
        
        feedback = FeedbackRecord(
            feedback_id=feedback_id,
            proposal_id=proposal_id,
            feedback_type=feedback_type,
            score=score,
            content=content,
            source=source
        )
        
        self.feedback_records.append(feedback)
        
        logger.info(
            f"Feedback submitted",
            extra={
                "feedback_id": feedback_id,
                "feedback_type": feedback_type.value,
                "score": score,
                "source": source
            }
        )
        
        # 触发优化分析
        await self._analyze_for_optimization(proposal_id, feedback)
        
        return feedback
    
    async def analyze_patterns(self) -> List[PatternAnalysis]:
        """
        分析错误模式
        
        Returns:
            模式分析结果列表
        """
        logger.info("Analyzing error patterns")
        
        # 统计错误类型
        error_type_count: Dict[str, List[ErrorRecord]] = {}
        for error in self.error_records:
            if error.error_type not in error_type_count:
                error_type_count[error.error_type] = []
            error_type_count[error.error_type].append(error)
        
        patterns: List[PatternAnalysis] = []
        
        for error_type, errors in error_type_count.items():
            # 统计影响的投标书
            affected_proposals = list(set(e.proposal_id for e in errors))
            
            # 统计未修复的错误
            unfixed_errors = [e for e in errors if not e.fixed]
            
            if unfixed_errors:  # 只分析未修复的错误
                # 分析根本原因（通过错误描述）
                root_cause = await self._identify_root_cause(unfixed_errors)
                
                # 生成预防策略
                prevention_strategy = await self._generate_prevention_strategy(
                    error_type, unfixed_errors
                )
                
                pattern = PatternAnalysis(
                    pattern_id=f"pat_{error_type}_{datetime.now().timestamp()}",
                    error_type=error_type,
                    frequency=len(unfixed_errors),
                    affected_proposals=affected_proposals,
                    root_cause=root_cause,
                    prevention_strategy=prevention_strategy
                )
                
                patterns.append(pattern)
        
        self.pattern_history.extend(patterns)
        
        logger.info(
            f"Pattern analysis completed",
            extra={"patterns_found": len(patterns)}
        )
        
        return patterns
    
    async def _identify_root_cause(
        self,
        errors: List[ErrorRecord]
    ) -> str:
        """使用LLM识别根本原因"""
        try:
            # 准备错误描述列表
            error_descriptions = [
                f"- {e.error_type}: {e.description} (位置: {e.location})"
                for e in errors[:10]  # 最多分析10个错误
            ]
            
            prompt = f"""分析以下错误记录，识别根本原因：

错误列表：
{chr(10).join(error_descriptions)}

请分析这些错误的共同特征和根本原因，用一句话总结（不超过50字）。"""
            
            # 使用DeepSeek进行分析（擅长理解和推理）
            root_cause = await self.llm_router.generate_text(
                prompt=prompt,
                system_prompt="你是一位经验丰富的质量分析专家，擅长发现问题的根本原因。",
                task_type=TaskType.FEEDBACK,
                temperature=0.3,
                model_name="deepseek"
            )
            
            logger.info(
                f"LLM identified root cause",
                extra={
                    "error_count": len(errors),
                    "root_cause": root_cause[:100],
                    "model": "deepseek"
                }
            )
            
            return root_cause.strip()
            
        except Exception as e:
            logger.warning(
                f"LLM root cause analysis failed, using fallback",
                extra={"error": str(e)}
            )
            # 降级到规则方法
            common_issues = {
                "missing_content": "内容缺失",
                "format_error": "格式错误",
                "constraint_violation": "约束违反",
                "spelling_error": "拼写错误",
                "logic_error": "逻辑错误"
            }
            
            keywords_count = {}
            for error in errors:
                for keyword, issue in common_issues.items():
                    if keyword in error.description.lower():
                        keywords_count[issue] = keywords_count.get(issue, 0) + 1
            
            if keywords_count:
                most_common_issue = max(keywords_count, key=keywords_count.get)
                return most_common_issue
            
            return "未知原因"
    
    async def _generate_prevention_strategy(
        self,
        error_type: str,
        errors: List[ErrorRecord]
    ) -> str:
        """使用LLM生成预防策略"""
        try:
            # 准备错误信息
            error_summary = f"错误类型: {error_type}, 出现次数: {len(errors)}"
            error_examples = [
                f"- {e.description}"
                for e in errors[:5]  # 最多5个例子
            ]
            
            prompt = f"""基于以下错误情况，提出具体的预防策略：

{error_summary}

错误示例：
{chr(10).join(error_examples)}

请提出2-3条可操作的预防措施（每条不超过30字）。"""
            
            # 使用千问生成建议（擅长分析和建议）
            strategy = await self.llm_router.generate_text(
                prompt=prompt,
                system_prompt="你是一位质量改进专家，擅长提出实用的预防措施和优化建议。",
                task_type=TaskType.ANALYSIS,
                temperature=0.4,
                model_name="qwen"
            )
            
            logger.info(
                f"LLM generated prevention strategy",
                extra={
                    "error_type": error_type,
                    "strategy_length": len(strategy),
                    "model": "qwen"
                }
            )
            
            return strategy.strip()
            
        except Exception as e:
            logger.warning(
                f"LLM strategy generation failed, using fallback",
                extra={"error_type": error_type, "error": str(e)}
            )
            # 降级到预定义策略
            strategies = {
                "missing_content": "增强内容检测机制，确保所有必需内容都被生成",
                "format_error": "加强格式验证，使用模板约束输出格式",
                "constraint_violation": "改进约束提取和检查逻辑",
                "spelling_error": "集成拼写检查工具，进行后处理校对",
                "logic_error": "增强逻辑验证，使用本体知识图谱进行一致性检查"
        }
        
        return strategies.get(error_type, "建立质量控制检查点")
    
    async def _analyze_for_optimization(
        self,
        proposal_id: str,
        feedback: FeedbackRecord
    ) -> Optional[OptimizationSuggestion]:
        """基于反馈分析优化机会"""
        # 如果反馈评分较低，生成优化建议
        if feedback.score < 70:
            suggestion = await self._generate_optimization_suggestion(
                proposal_id, feedback
            )
            if suggestion:
                self.optimization_suggestions.append(suggestion)
            return suggestion
        
        return None
    
    async def _generate_optimization_suggestion(
        self,
        proposal_id: str,
        feedback: FeedbackRecord
    ) -> Optional[OptimizationSuggestion]:
        """生成优化建议"""
        # 根据反馈类型和分数生成建议
        categories = {
            FeedbackType.POSITIVE: "GENERATION",
            FeedbackType.NEGATIVE: "GENERATION",
            FeedbackType.CORRECTIVE: "SCORING",
            FeedbackType.QUALITY_IMPROVEMENT: "COMPARISON"
        }
        
        category = categories.get(feedback.feedback_type, "GENERATION")
        
        # 根据反馈分数确定优先级
        if feedback.score < 50:
            priority = "HIGH"
            expected_impact_improve = 20
        elif feedback.score < 70:
            priority = "MEDIUM"
            expected_impact_improve = 10
        else:
            priority = "LOW"
            expected_impact_improve = 5
        
        suggestion = OptimizationSuggestion(
            suggestion_id=f"sug_{proposal_id}_{datetime.now().timestamp()}",
            category=category,
            priority=priority,
            description=f"根据用户反馈（评分 {feedback.score}），建议优化 {category} 模块",
            expected_impact={
                "score_improvement": expected_impact_improve,
                "efficiency_gain": 5
            },
            implementation_cost="MEDIUM",
            confidence=80.0 if feedback.source == "USER" else 70.0
        )
        
        logger.info(
            f"Optimization suggestion generated",
            extra={
                "suggestion_id": suggestion.suggestion_id,
                "category": category,
                "priority": priority
            }
        )
        
        return suggestion
    
    async def get_improvement_recommendations(
        self,
        days: int = 7
    ) -> Dict:
        """
        获取改进建议
        
        Args:
            days: 统计周期（天数）
            
        Returns:
            改进建议
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        recent_errors = [e for e in self.error_records if e.first_occurred >= cutoff_time]
        recent_feedback = [f for f in self.feedback_records if f.created_at >= cutoff_time]
        
        # 统计错误类型分布
        error_types = {}
        for error in recent_errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        # 统计平均反馈评分
        avg_feedback_score = (
            sum(f.score for f in recent_feedback) / len(recent_feedback)
            if recent_feedback else 0
        )
        
        recommendations = {
            "period_days": days,
            "total_errors": len(recent_errors),
            "total_feedback": len(recent_feedback),
            "avg_feedback_score": avg_feedback_score,
            "error_distribution": error_types,
            "critical_errors": len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]),
            "suggestions": [
                s.dict() for s in self.optimization_suggestions
                if s.confidence > 70
            ][-10:]  # 返回最后10条高可信度建议
        }
        
        return recommendations
    
    async def apply_improvement(
        self,
        suggestion_id: str,
        implementation_details: Dict
    ) -> Dict:
        """
        应用改进
        
        Args:
            suggestion_id: 建议ID
            implementation_details: 实施细节
            
        Returns:
            应用结果
        """
        suggestion = next(
            (s for s in self.optimization_suggestions if s.suggestion_id == suggestion_id),
            None
        )
        
        if not suggestion:
            logger.error(f"Suggestion {suggestion_id} not found")
            return {"error": "Suggestion not found"}
        
        logger.info(
            f"Applying improvement",
            extra={
                "suggestion_id": suggestion_id,
                "category": suggestion.category
            }
        )
        
        # 模拟应用改进的过程
        result = {
            "suggestion_id": suggestion_id,
            "status": "applied",
            "implementation_details": implementation_details,
            "expected_improvement": suggestion.expected_impact,
            "applied_at": datetime.now().isoformat(),
            "monitoring_period": "7 days"
        }
        
        return result
    
    async def get_model_performance_metrics(self) -> Dict:
        """获取模型性能指标"""
        total_proposals_with_errors = len(set(e.proposal_id for e in self.error_records))
        total_proposals_with_feedback = len(set(f.proposal_id for f in self.feedback_records))
        
        metrics = {
            "total_error_records": len(self.error_records),
            "total_feedback_records": len(self.feedback_records),
            "avg_error_severity": "MINOR",  # 实际计算
            "critical_errors_count": len([e for e in self.error_records if e.severity == ErrorSeverity.CRITICAL]),
            "fixed_errors_count": len([e for e in self.error_records if e.fixed]),
            "patterns_identified": len(self.pattern_history),
            "improvement_suggestions": len(self.optimization_suggestions),
            "avg_feedback_score": (
                sum(f.score for f in self.feedback_records) / len(self.feedback_records)
                if self.feedback_records else 0
            )
        }
        
        return metrics

