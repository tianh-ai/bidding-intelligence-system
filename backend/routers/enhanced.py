"""
增强功能路由
生成、评分、对比、强化学习反馈相关的 API 端点
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from engines.generation_engine import (
    GenerationEngine, GenerationStrategy, GenerationMode
)
from engines.scoring_engine import ScoringEngine
from engines.comparison_engine import ComparisonEngine
from engines.reinforcement_feedback import (
    ReinforcementLearningFeedback, FeedbackType, ErrorSeverity
)
from core.logger import logger

# 初始化路由
router = APIRouter()

# 初始化引擎实例
generation_engine = GenerationEngine()
scoring_engine = ScoringEngine()
comparison_engine = ComparisonEngine()
feedback_engine = ReinforcementLearningFeedback()


# ==================== 生成相关端点 ====================

class GenerateProposalRequest(BaseModel):
    """生成投标书请求"""
    tender_id: str = Field(..., description="招标书ID")
    template_id: str = Field(..., description="模板ID")
    strategy: str = Field(default="balanced", description="生成策略: conservative/balanced/creative")
    mode: str = Field(default="full", description="生成模式: full/partial/incremental")
    options: Optional[Dict] = Field(None, description="额外选项")


@router.post("/generate/proposal", tags=["生成"])
async def generate_proposal(request: GenerateProposalRequest):
    """生成投标书"""
    try:
        strategy = GenerationStrategy(request.strategy)
        mode = GenerationMode(request.mode)
        
        version = await generation_engine.generate_proposal(
            tender_id=request.tender_id,
            template_id=request.template_id,
            strategy=strategy,
            mode=mode,
            options=request.options
        )
        
        return {
            "status": "success",
            "version_id": version.version_id,
            "overall_score": version.overall_score,
            "content_count": len(version.contents),
            "generated_at": version.generated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/history/{tender_id}", tags=["生成"])
async def get_generation_history(tender_id: str, limit: int = 10):
    """获取生成历史"""
    history = await generation_engine.get_generation_history(tender_id, limit)
    return {"status": "success", "history": history}


@router.post("/generate/compare", tags=["生成"])
async def compare_versions(version_id_1: str, version_id_2: str):
    """对比两个生成版本"""
    try:
        comparison = await generation_engine.compare_versions(version_id_1, version_id_2)
        return {"status": "success", "comparison": comparison}
    except Exception as e:
        logger.error(f"Error comparing versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 评分相关端点 ====================

class ScoreProposalRequest(BaseModel):
    """评分投标书请求"""
    proposal_id: str = Field(..., description="投标书ID")
    tender_id: str = Field(..., description="招标书ID")
    proposal_content: Dict = Field(..., description="投标书内容")
    comparison_set: Optional[List[Dict]] = Field(None, description="对标集合")


@router.post("/score/proposal", tags=["评分"])
async def score_proposal(request: ScoreProposalRequest):
    """评分投标书"""
    try:
        score = await scoring_engine.score_proposal(
            proposal_id=request.proposal_id,
            tender_id=request.tender_id,
            proposal_content=request.proposal_content,
            comparison_set=request.comparison_set
        )
        
        return {
            "status": "success",
            "score_id": score.score_id,
            "overall_score": score.overall_score,
            "hard_metric_pass": score.hard_metric_pass,
            "scored_at": score.scored_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error scoring proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/compare", tags=["评分"])
async def compare_proposals_score(proposal_id_1: str, proposal_id_2: str):
    """对比两个投标书的评分"""
    try:
        comparison = await scoring_engine.compare_proposals(
            proposal_id_1, proposal_id_2
        )
        return {
            "status": "success",
            "comparison": comparison.dict()
        }
    except Exception as e:
        logger.error(f"Error comparing proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/report/{tender_id}", tags=["评分"])
async def get_scoring_report(tender_id: str):
    """获取评分报告"""
    try:
        report = await scoring_engine.get_scoring_report(tender_id)
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"Error getting scoring report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 对比分析相关端点 ====================

class CompareDocumentsRequest(BaseModel):
    """对比文档请求"""
    doc1_id: str = Field(..., description="文档1 ID")
    doc1_content: Dict = Field(..., description="文档1内容")
    doc2_id: str = Field(..., description="文档2 ID")
    doc2_content: Dict = Field(..., description="文档2内容")
    detailed: bool = Field(default=True, description="是否详细对比")


@router.post("/compare/documents", tags=["对比"])
async def compare_documents(request: CompareDocumentsRequest):
    """对比两份文档"""
    try:
        comparison = await comparison_engine.compare_documents(
            doc1_id=request.doc1_id,
            doc1_content=request.doc1_content,
            doc2_id=request.doc2_id,
            doc2_content=request.doc2_content,
            detailed=request.detailed
        )
        
        return {
            "status": "success",
            "comparison_id": comparison.comparison_id,
            "overall_similarity": comparison.overall_similarity,
            "similarity_level": comparison.similarity_level.value,
            "total_differences": comparison.total_differences,
            "heatmap_data": comparison.heatmap_data
        }
    except Exception as e:
        logger.error(f"Error comparing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/summary/{comparison_id}", tags=["对比"])
async def get_comparison_summary(comparison_id: str):
    """获取对比总结"""
    try:
        summary = await comparison_engine.get_comparison_summary(comparison_id)
        return {
            "status": "success",
            "summary": summary.dict()
        }
    except Exception as e:
        logger.error(f"Error getting comparison summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/history", tags=["对比"])
async def get_comparison_history(limit: int = 10):
    """获取对比历史"""
    history = await comparison_engine.get_comparison_history(limit)
    return {"status": "success", "history": history}


# ==================== 强化学习反馈相关端点 ====================

class RecordErrorRequest(BaseModel):
    """记录错误请求"""
    proposal_id: str = Field(..., description="投标书ID")
    error_type: str = Field(..., description="错误类型")
    severity: str = Field(..., description="严重程度: critical/major/minor/info")
    description: str = Field(..., description="错误描述")
    location: str = Field(..., description="错误位置")
    correction: Optional[str] = Field(None, description="纠正方案")


@router.post("/feedback/error", tags=["反馈"])
async def record_error(request: RecordErrorRequest):
    """记录错误"""
    try:
        error = await feedback_engine.record_error(
            proposal_id=request.proposal_id,
            error_type=request.error_type,
            severity=ErrorSeverity(request.severity),
            description=request.description,
            location=request.location,
            correction=request.correction
        )
        
        return {
            "status": "success",
            "error_id": error.error_id,
            "occurrence_count": error.occurrence_count
        }
    except Exception as e:
        logger.error(f"Error recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SubmitFeedbackRequest(BaseModel):
    """提交反馈请求"""
    proposal_id: str = Field(..., description="投标书ID")
    feedback_type: str = Field(..., description="反馈类型: positive/negative/corrective/quality_improvement")
    score: float = Field(..., ge=0, le=100, description="评分 0-100")
    content: str = Field(..., description="反馈内容")
    source: str = Field(default="USER", description="反馈来源: SYSTEM/USER/EVALUATOR")


@router.post("/feedback/submit", tags=["反馈"])
async def submit_feedback(request: SubmitFeedbackRequest):
    """提交反馈"""
    try:
        feedback = await feedback_engine.submit_feedback(
            proposal_id=request.proposal_id,
            feedback_type=FeedbackType(request.feedback_type),
            score=request.score,
            content=request.content,
            source=request.source
        )
        
        return {
            "status": "success",
            "feedback_id": feedback.feedback_id,
            "created_at": feedback.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/analyze-patterns", tags=["反馈"])
async def analyze_patterns():
    """分析错误模式"""
    try:
        patterns = await feedback_engine.analyze_patterns()
        return {
            "status": "success",
            "patterns": [p.dict() for p in patterns]
        }
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/recommendations", tags=["反馈"])
async def get_recommendations(days: int = 7):
    """获取改进建议"""
    try:
        recommendations = await feedback_engine.get_improvement_recommendations(days)
        return {
            "status": "success",
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/apply-improvement", tags=["反馈"])
async def apply_improvement(suggestion_id: str, implementation_details: Dict):
    """应用改进建议"""
    try:
        result = await feedback_engine.apply_improvement(
            suggestion_id, implementation_details
        )
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error applying improvement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/metrics", tags=["反馈"])
async def get_model_metrics():
    """获取模型性能指标"""
    try:
        metrics = await feedback_engine.get_model_performance_metrics()
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

