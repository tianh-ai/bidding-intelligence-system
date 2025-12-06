"""
评分引擎 (Scoring Engine)
多维度自动评分系统
支持硬指标、软指标、对标评分
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from core.logger import logger
from core.llm_router import get_llm_router, TaskType


class DimensionType(str, Enum):
    """评分维度类型"""
    TECHNICAL = "technical"  # 技术维度
    COMMERCIAL = "commercial"  # 商务维度
    COMPLIANCE = "compliance"  # 合规维度
    INNOVATION = "innovation"  # 创新维度
    PRESENTATION = "presentation"  # 呈现维度


class ScoringCriteria(BaseModel):
    """评分标准"""
    criteria_id: str = Field(..., description="标准ID")
    name: str = Field(..., description="标准名称")
    dimension: DimensionType = Field(..., description="维度")
    description: str = Field(..., description="描述")
    weight: float = Field(..., ge=0, le=1, description="权重")
    hard_metric: bool = Field(..., description="是否硬指标")
    max_score: float = Field(..., ge=0, le=100, description="最高分")
    benchmark: Optional[float] = Field(None, description="对标值")


class DimensionScore(BaseModel):
    """维度评分"""
    dimension: DimensionType = Field(..., description="维度")
    score: float = Field(..., ge=0, le=100, description="得分 0-100")
    weight: float = Field(..., ge=0, le=1, description="权重")
    weighted_score: float = Field(..., description="加权分")
    details: Dict = Field(default_factory=dict, description="详细信息")


class ProposalScore(BaseModel):
    """投标书评分"""
    score_id: str = Field(..., description="评分ID")
    proposal_id: str = Field(..., description="投标书ID")
    tender_id: str = Field(..., description="招标书ID")
    overall_score: float = Field(..., ge=0, le=100, description="总体评分")
    dimension_scores: List[DimensionScore] = Field(..., description="维度评分列表")
    hard_metric_pass: bool = Field(..., description="硬指标是否全部通过")
    rank: Optional[int] = Field(None, description="排名")
    benchmark_comparison: Dict = Field(default_factory=dict, description="对标对比")
    scoring_details: Dict = Field(default_factory=dict, description="评分详情")
    scored_at: datetime = Field(default_factory=datetime.now)


class ScoringComparison(BaseModel):
    """评分对比"""
    comparison_id: str = Field(..., description="对比ID")
    proposal_1_id: str = Field(..., description="投标书1 ID")
    proposal_2_id: str = Field(..., description="投标书2 ID")
    score_1: float = Field(..., description="投标书1评分")
    score_2: float = Field(..., description="投标书2评分")
    dimension_comparison: Dict = Field(..., description="维度对比")
    recommendation: str = Field(..., description="推荐")


class ScoringEngine:
    """
    自动评分引擎
    
    功能：
    - 多维度自动评分（技术、商务、合规、创新、呈现）
    - 硬指标检查（必须满足）
    - 软指标评分（LLM 评估）
    - 对标分析（与行业水平对比）
    - 评分溯源（可查看评分理由）
    """
    
    def __init__(self):
        """初始化评分引擎"""
        logger.info("ScoringEngine initialized")
        self.scoring_history: List[ProposalScore] = []
        self.scoring_criteria = self._initialize_criteria()
        self.llm_router = get_llm_router()  # 获取LLM路由器
        logger.info("LLM Router integrated into ScoringEngine")
    
    def _initialize_criteria(self) -> List[ScoringCriteria]:
        """初始化评分标准"""
        return [
            # 技术维度 (25%)
            ScoringCriteria(
                criteria_id="tech_001",
                name="技术方案完整性",
                dimension=DimensionType.TECHNICAL,
                description="技术方案是否完整、清晰、具有可行性",
                weight=0.15,
                hard_metric=False,
                max_score=100,
                benchmark=85.0
            ),
            ScoringCriteria(
                criteria_id="tech_002",
                name="系统架构设计",
                dimension=DimensionType.TECHNICAL,
                description="系统架构是否先进、合理、可扩展",
                weight=0.07,
                hard_metric=False,
                max_score=100,
                benchmark=80.0
            ),
            ScoringCriteria(
                criteria_id="tech_003",
                name="性能指标达成",
                dimension=DimensionType.TECHNICAL,
                description="是否满足招标书性能要求",
                weight=0.03,
                hard_metric=True,
                max_score=100,
                benchmark=90.0
            ),
            
            # 商务维度 (20%)
            ScoringCriteria(
                criteria_id="comm_001",
                name="价格竞争力",
                dimension=DimensionType.COMMERCIAL,
                description="价格是否具有竞争力",
                weight=0.15,
                hard_metric=False,
                max_score=100,
                benchmark=75.0
            ),
            ScoringCriteria(
                criteria_id="comm_002",
                name="支付条款合理性",
                dimension=DimensionType.COMMERCIAL,
                description="支付条款是否合理、灵活",
                weight=0.05,
                hard_metric=False,
                max_score=100,
                benchmark=70.0
            ),
            
            # 合规维度 (20%)
            ScoringCriteria(
                criteria_id="comp_001",
                name="资质合规性",
                dimension=DimensionType.COMPLIANCE,
                description="投标人资质是否满足招标要求",
                weight=0.12,
                hard_metric=True,
                max_score=100,
                benchmark=95.0
            ),
            ScoringCriteria(
                criteria_id="comp_002",
                name="文件完整性",
                dimension=DimensionType.COMPLIANCE,
                description="投标文件是否完整、符合格式要求",
                weight=0.08,
                hard_metric=True,
                max_score=100,
                benchmark=98.0
            ),
            
            # 创新维度 (20%)
            ScoringCriteria(
                criteria_id="inno_001",
                name="创新方案",
                dimension=DimensionType.INNOVATION,
                description="是否提出创新的解决方案",
                weight=0.20,
                hard_metric=False,
                max_score=100,
                benchmark=60.0
            ),
            
            # 呈现维度 (15%)
            ScoringCriteria(
                criteria_id="pres_001",
                name="呈现质量",
                dimension=DimensionType.PRESENTATION,
                description="文档排版、图表质量等呈现质量",
                weight=0.15,
                hard_metric=False,
                max_score=100,
                benchmark=75.0
            )
        ]
    
    async def score_proposal(
        self,
        proposal_id: str,
        tender_id: str,
        proposal_content: Dict,
        comparison_set: Optional[List[Dict]] = None
    ) -> ProposalScore:
        """
        评分投标书
        
        Args:
            proposal_id: 投标书ID
            tender_id: 招标书ID
            proposal_content: 投标书内容
            comparison_set: 对标集合（用于对标分析）
            
        Returns:
            评分结果
        """
        logger.info(
            f"Scoring proposal {proposal_id}",
            extra={"tender_id": tender_id}
        )
        
        score_id = f"score_{proposal_id}_{datetime.now().timestamp()}"
        
        # 检查硬指标
        hard_metric_pass, hard_metric_details = await self._check_hard_metrics(
            proposal_content
        )
        
        # 计算各维度评分
        dimension_scores: List[DimensionScore] = []
        scoring_details = {}
        
        for dimension in DimensionType:
            criteria_for_dim = [
                c for c in self.scoring_criteria
                if c.dimension == dimension
            ]
            
            if criteria_for_dim:
                dim_score = await self._score_dimension(
                    dimension, criteria_for_dim, proposal_content
                )
                dimension_scores.append(dim_score)
                scoring_details[dimension.value] = dim_score.details
        
        # 计算总体评分
        overall_score = sum(
            ds.weighted_score for ds in dimension_scores
        )
        
        # 对标分析
        benchmark_comparison = {}
        if comparison_set:
            benchmark_comparison = await self._benchmark_analysis(
                proposal_content, comparison_set, dimension_scores
            )
        
        # 创建评分对象
        score = ProposalScore(
            score_id=score_id,
            proposal_id=proposal_id,
            tender_id=tender_id,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            hard_metric_pass=hard_metric_pass,
            benchmark_comparison=benchmark_comparison,
            scoring_details=scoring_details
        )
        
        # 保存评分历史
        self.scoring_history.append(score)
        
        logger.info(
            f"Proposal scored",
            extra={
                "score_id": score_id,
                "overall_score": overall_score,
                "hard_metric_pass": hard_metric_pass
            }
        )
        
        return score
    
    async def _check_hard_metrics(
        self,
        proposal_content: Dict
    ) -> Tuple[bool, Dict]:
        """检查硬指标"""
        hard_criteria = [c for c in self.scoring_criteria if c.hard_metric]
        details = {}
        
        all_pass = True
        for criteria in hard_criteria:
            # 简单的检查逻辑（实际实现需要更复杂的验证）
            passed = proposal_content.get(f"metric_{criteria.criteria_id}", False)
            details[criteria.criteria_id] = {
                "name": criteria.name,
                "passed": passed,
                "required": True
            }
            if not passed:
                all_pass = False
        
        return all_pass, details
    
    async def _score_dimension(
        self,
        dimension: DimensionType,
        criteria_list: List[ScoringCriteria],
        proposal_content: Dict
    ) -> DimensionScore:
        """评分单个维度"""
        dimension_details = {}
        weighted_scores = []
        
        for criteria in criteria_list:
            # 模拟评分（实际实现使用 LLM）
            score = await self._score_criteria(
                criteria, proposal_content
            )
            weighted_score = score * criteria.weight
            weighted_scores.append(weighted_score)
            
            dimension_details[criteria.criteria_id] = {
                "name": criteria.name,
                "score": score,
                "weight": criteria.weight,
                "weighted_score": weighted_score
            }
        
        # 计算维度总分（归一化到 0-100）
        total_weight = sum(c.weight for c in criteria_list)
        dimension_score = (
            sum(weighted_scores) / total_weight
            if total_weight > 0 else 0
        )
        
        # 维度权重（所有标准的权重之和）
        dimension_weight = total_weight
        
        return DimensionScore(
            dimension=dimension,
            score=dimension_score,
            weight=dimension_weight,
            weighted_score=dimension_score * dimension_weight,
            details=dimension_details
        )
    
    async def _score_criteria(
        self,
        criteria: ScoringCriteria,
        proposal_content: Dict
    ) -> float:
        """评分单项标准 - 使用LLM进行智能评分"""
        
        # 如果是硬指标，直接检查
        if criteria.hard_metric:
            metric_key = f"metric_{criteria.criteria_id}"
            if metric_key in proposal_content:
                return 100.0 if proposal_content[metric_key] else 0.0
        
        # 软指标使用LLM评分
        try:
            # 提取要评分的内容
            content_to_score = proposal_content.get("content", "")
            if not content_to_score:
                content_to_score = str(proposal_content)
            
            # 使用千问进行评分（擅长分析和评估）
            result = await self.llm_router.score_content(
                content=content_to_score[:2000],  # 限制长度
                criteria=f"{criteria.name}: {criteria.description}",
                context=f"评分维度: {criteria.dimension.value}, 权重: {criteria.weight}"
            )
            
            score = result["score"]
            
            logger.info(
                f"LLM scored criteria {criteria.criteria_id}",
                extra={
                    "criteria": criteria.name,
                    "score": score,
                    "model": result["model"],
                    "reasoning": result["reasoning"][:100]
                }
            )
            
            return min(criteria.max_score, score)
            
        except Exception as e:
            logger.warning(
                f"LLM scoring failed, using fallback",
                extra={"criteria": criteria.criteria_id, "error": str(e)}
            )
            # 降级到简单评分
            content_quality = proposal_content.get("quality_score", 70)
            relevance = proposal_content.get("relevance_score", 75)
            completeness = proposal_content.get("completeness_score", 80)
            score = (content_quality * 0.4 + relevance * 0.3 + completeness * 0.3)
            return min(criteria.max_score, score)
    
    async def _benchmark_analysis(
        self,
        proposal_content: Dict,
        comparison_set: List[Dict],
        dimension_scores: List[DimensionScore]
    ) -> Dict:
        """对标分析"""
        analysis = {
            "sample_size": len(comparison_set),
            "comparison_results": []
        }
        
        for i, comparison in enumerate(comparison_set):
            comparison_score = sum(
                ds.weighted_score for ds in dimension_scores
            ) / len(dimension_scores) if dimension_scores else 0
            
            comparison_results = {
                "benchmark_id": f"bench_{i}",
                "our_score": comparison_score,
                "benchmark_score": comparison.get("score", 70),
                "difference": comparison_score - comparison.get("score", 70),
                "rank": "above" if comparison_score > comparison.get("score", 70) else "below"
            }
            analysis["comparison_results"].append(comparison_results)
        
        return analysis
    
    async def compare_proposals(
        self,
        proposal_id_1: str,
        proposal_id_2: str
    ) -> ScoringComparison:
        """
        对比两个投标书
        
        Args:
            proposal_id_1: 投标书1 ID
            proposal_id_2: 投标书2 ID
            
        Returns:
            对比结果
        """
        score_1 = next(
            (s for s in self.scoring_history if s.proposal_id == proposal_id_1),
            None
        )
        score_2 = next(
            (s for s in self.scoring_history if s.proposal_id == proposal_id_2),
            None
        )
        
        if not score_1 or not score_2:
            logger.error("Score not found for comparison")
            raise ValueError("One or both proposals not found")
        
        # 维度对比
        dimension_comparison = {}
        for dim in DimensionType:
            ds1 = next((ds for ds in score_1.dimension_scores if ds.dimension == dim), None)
            ds2 = next((ds for ds in score_2.dimension_scores if ds.dimension == dim), None)
            
            if ds1 and ds2:
                dimension_comparison[dim.value] = {
                    "score_1": ds1.score,
                    "score_2": ds2.score,
                    "difference": ds2.score - ds1.score,
                    "winner": "proposal_2" if ds2.score > ds1.score else "proposal_1"
                }
        
        # 生成推荐
        score_diff = score_2.overall_score - score_1.overall_score
        if abs(score_diff) < 3:
            recommendation = "两个投标书评分接近，需要其他因素判断"
        elif score_diff > 5:
            recommendation = "投标书2更优，建议优先选择"
        else:
            recommendation = "投标书1相对较优，建议选择投标书1"
        
        comparison = ScoringComparison(
            comparison_id=f"comp_{proposal_id_1}_{proposal_id_2}",
            proposal_1_id=proposal_id_1,
            proposal_2_id=proposal_id_2,
            score_1=score_1.overall_score,
            score_2=score_2.overall_score,
            dimension_comparison=dimension_comparison,
            recommendation=recommendation
        )
        
        logger.info(
            f"Proposals compared",
            extra={
                "proposal_1": proposal_id_1,
                "score_1": score_1.overall_score,
                "proposal_2": proposal_id_2,
                "score_2": score_2.overall_score
            }
        )
        
        return comparison
    
    async def get_scoring_report(
        self,
        tender_id: str
    ) -> Dict:
        """获取评分报告"""
        tender_scores = [s for s in self.scoring_history if s.tender_id == tender_id]
        
        if not tender_scores:
            return {"error": "No scores found for this tender"}
        
        # 排序并添加排名
        tender_scores_sorted = sorted(
            tender_scores, key=lambda s: s.overall_score, reverse=True
        )
        
        for i, score in enumerate(tender_scores_sorted, 1):
            score.rank = i
        
        report = {
            "tender_id": tender_id,
            "total_proposals": len(tender_scores),
            "scores": [
                {
                    "proposal_id": s.proposal_id,
                    "overall_score": s.overall_score,
                    "rank": s.rank,
                    "hard_metric_pass": s.hard_metric_pass,
                    "dimension_scores": {
                        ds.dimension.value: ds.score
                        for ds in s.dimension_scores
                    }
                }
                for s in tender_scores_sorted
            ],
            "benchmark_info": {
                "average_score": sum(s.overall_score for s in tender_scores) / len(tender_scores),
                "max_score": max(s.overall_score for s in tender_scores),
                "min_score": min(s.overall_score for s in tender_scores)
            }
        }
        
        return report

