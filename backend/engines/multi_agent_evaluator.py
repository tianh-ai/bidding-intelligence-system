"""
多代理评估器（Multi-Agent Evaluator）
三层检查架构：硬约束检查 + 软约束检查 + 图谱验证
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import re
import openai

from core.logger import logger
from core.config import settings
from db.ontology import OntologyManager


# ========== 检查结果枚举 ==========

class CheckStatus(str, Enum):
    """检查状态"""
    PASS = "pass"              # 通过
    FAIL = "fail"              # 失败
    WARNING = "warning"        # 警告
    INFO = "info"              # 信息


class CheckLevel(str, Enum):
    """检查级别"""
    CRITICAL = "critical"      # 关键（硬约束）
    IMPORTANT = "important"    # 重要（软约束）
    MINOR = "minor"            # 次要


# ========== Pydantic模型 ==========

class CheckResult(BaseModel):
    """单个检查结果"""
    check_id: str
    check_name: str
    check_level: CheckLevel
    status: CheckStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None  # 0-100


class EvaluationReport(BaseModel):
    """评估报告"""
    proposal_id: str
    tender_id: str
    hard_constraint_results: List[CheckResult]
    soft_constraint_results: List[CheckResult]
    kg_validation_results: List[CheckResult]
    overall_score: float  # 0-100
    overall_status: CheckStatus
    recommendations: List[str] = Field(default_factory=list)
    created_at: str


# ========== 硬约束检查器 ==========

class HardConstraintChecker:
    """
    硬约束检查器
    使用确定性规则检查硬性要求（Python代码）
    """
    
    def __init__(self):
        logger.info("HardConstraintChecker initialized")
    
    async def check(self, proposal: Dict[str, Any], tender: Dict[str, Any]) -> List[CheckResult]:
        """
        检查硬约束
        
        Args:
            proposal: 投标文件
            tender: 招标文件
            
        Returns:
            检查结果列表
        """
        results = []
        
        # 1. 检查必填字段
        results.append(await self._check_required_fields(proposal, tender))
        
        # 2. 检查资质证书
        results.append(await self._check_qualifications(proposal, tender))
        
        # 3. 检查价格范围
        results.append(await self._check_price_range(proposal, tender))
        
        # 4. 检查格式要求
        results.append(await self._check_format_compliance(proposal, tender))
        
        logger.info(f"Hard constraint checks completed: {len(results)} checks")
        return results
    
    async def _check_required_fields(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> CheckResult:
        """检查必填字段"""
        required_fields = tender.get("required_fields", [])
        missing_fields = []
        
        for field in required_fields:
            if field not in proposal or not proposal[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return CheckResult(
                check_id="hard_01",
                check_name="必填字段检查",
                check_level=CheckLevel.CRITICAL,
                status=CheckStatus.FAIL,
                message=f"缺少{len(missing_fields)}个必填字段",
                details={"missing_fields": missing_fields},
                score=0.0
            )
        
        return CheckResult(
            check_id="hard_01",
            check_name="必填字段检查",
            check_level=CheckLevel.CRITICAL,
            status=CheckStatus.PASS,
            message="所有必填字段已提供",
            score=100.0
        )
    
    async def _check_qualifications(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> CheckResult:
        """检查资质证书"""
        required_certs = tender.get("required_certifications", [])
        provided_certs = proposal.get("certifications", [])
        
        missing_certs = [cert for cert in required_certs if cert not in provided_certs]
        
        if missing_certs:
            return CheckResult(
                check_id="hard_02",
                check_name="资质证书检查",
                check_level=CheckLevel.CRITICAL,
                status=CheckStatus.FAIL,
                message=f"缺少{len(missing_certs)}项必需资质",
                details={"missing_certifications": missing_certs},
                score=0.0
            )
        
        return CheckResult(
            check_id="hard_02",
            check_name="资质证书检查",
            check_level=CheckLevel.CRITICAL,
            status=CheckStatus.PASS,
            message="所有必需资质已提供",
            score=100.0
        )
    
    async def _check_price_range(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> CheckResult:
        """检查价格范围"""
        max_price = tender.get("max_budget")
        proposed_price = proposal.get("total_price")
        
        if not max_price or not proposed_price:
            return CheckResult(
                check_id="hard_03",
                check_name="价格范围检查",
                check_level=CheckLevel.CRITICAL,
                status=CheckStatus.WARNING,
                message="缺少价格信息",
                score=50.0
            )
        
        if proposed_price > max_price:
            return CheckResult(
                check_id="hard_03",
                check_name="价格范围检查",
                check_level=CheckLevel.CRITICAL,
                status=CheckStatus.FAIL,
                message=f"报价{proposed_price}超过预算上限{max_price}",
                details={"proposed": proposed_price, "max": max_price},
                score=0.0
            )
        
        return CheckResult(
            check_id="hard_03",
            check_name="价格范围检查",
            check_level=CheckLevel.CRITICAL,
            status=CheckStatus.PASS,
            message=f"报价{proposed_price}在预算范围内",
            score=100.0
        )
    
    async def _check_format_compliance(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> CheckResult:
        """检查格式要求"""
        format_reqs = tender.get("format_requirements", {})
        issues = []
        
        # 检查页数限制
        if "max_pages" in format_reqs:
            max_pages = format_reqs["max_pages"]
            actual_pages = proposal.get("page_count", 0)
            if actual_pages > max_pages:
                issues.append(f"页数{actual_pages}超过限制{max_pages}")
        
        # 检查文件格式
        if "allowed_formats" in format_reqs:
            allowed = format_reqs["allowed_formats"]
            file_format = proposal.get("file_format", "")
            if file_format not in allowed:
                issues.append(f"文件格式{file_format}不符合要求")
        
        if issues:
            return CheckResult(
                check_id="hard_04",
                check_name="格式要求检查",
                check_level=CheckLevel.IMPORTANT,
                status=CheckStatus.FAIL,
                message=f"发现{len(issues)}个格式问题",
                details={"issues": issues},
                score=0.0
            )
        
        return CheckResult(
            check_id="hard_04",
            check_name="格式要求检查",
            check_level=CheckLevel.IMPORTANT,
            status=CheckStatus.PASS,
            message="格式符合要求",
            score=100.0
        )


# ========== 软约束检查器 ==========

class SoftConstraintChecker:
    """
    软约束检查器
    使用LLM进行语义理解和评分
    """
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("SoftConstraintChecker initialized")
    
    async def check(self, proposal: Dict[str, Any], tender: Dict[str, Any]) -> List[CheckResult]:
        """
        检查软约束
        
        Args:
            proposal: 投标文件
            tender: 招标文件
            
        Returns:
            检查结果列表
        """
        results = []
        
        # 1. 技术方案完整性
        results.append(await self._check_technical_completeness(proposal, tender))
        
        # 2. 内容相关性
        results.append(await self._check_content_relevance(proposal, tender))
        
        # 3. 专业性评估
        results.append(await self._check_professionalism(proposal))
        
        # 4. 创新性评估
        results.append(await self._check_innovation(proposal, tender))
        
        logger.info(f"Soft constraint checks completed: {len(results)} checks")
        return results
    
    async def _check_technical_completeness(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> CheckResult:
        """检查技术方案完整性（LLM评分）"""
        prompt = f"""
请评估投标文件的技术方案完整性：

**招标要求**：
{tender.get('technical_requirements', '未提供')}

**投标方案**：
{proposal.get('technical_solution', '未提供')}

**评分标准**（0-100分）：
- 90-100: 方案完整，覆盖所有要点
- 70-89: 方案较完整，有少量遗漏
- 50-69: 方案基本完整，有明显遗漏
- 0-49: 方案不完整，大量遗漏

请给出分数和简要理由。
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "你是专业的技术评审专家"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        
        # 解析分数（简单正则）
        score_match = re.search(r'(\d+)分', result_text)
        score = float(score_match.group(1)) if score_match else 70.0
        
        status = CheckStatus.PASS if score >= 70 else CheckStatus.WARNING
        
        return CheckResult(
            check_id="soft_01",
            check_name="技术方案完整性",
            check_level=CheckLevel.IMPORTANT,
            status=status,
            message=result_text[:200],
            score=score
        )
    
    async def _check_content_relevance(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> CheckResult:
        """检查内容相关性"""
        # 简化实现：检查关键词匹配度
        tender_keywords = set(tender.get('keywords', []))
        proposal_text = str(proposal.get('content', ''))
        
        matched_keywords = [kw for kw in tender_keywords if kw in proposal_text]
        relevance_score = (len(matched_keywords) / len(tender_keywords) * 100) if tender_keywords else 100
        
        status = CheckStatus.PASS if relevance_score >= 60 else CheckStatus.WARNING
        
        return CheckResult(
            check_id="soft_02",
            check_name="内容相关性检查",
            check_level=CheckLevel.IMPORTANT,
            status=status,
            message=f"匹配了{len(matched_keywords)}/{len(tender_keywords)}个关键词",
            details={"matched_keywords": matched_keywords},
            score=relevance_score
        )
    
    async def _check_professionalism(self, proposal: Dict[str, Any]) -> CheckResult:
        """检查专业性"""
        # 简化实现：检查是否包含专业术语
        content = str(proposal.get('content', ''))
        
        professional_terms = [
            "技术方案", "实施方案", "质量保证", "项目管理",
            "技术参数", "性能指标", "验收标准", "售后服务"
        ]
        
        found_terms = [term for term in professional_terms if term in content]
        score = (len(found_terms) / len(professional_terms) * 100)
        
        status = CheckStatus.PASS if score >= 50 else CheckStatus.WARNING
        
        return CheckResult(
            check_id="soft_03",
            check_name="专业性评估",
            check_level=CheckLevel.MINOR,
            status=status,
            message=f"包含{len(found_terms)}个专业术语",
            score=score
        )
    
    async def _check_innovation(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> CheckResult:
        """检查创新性"""
        # 简化实现：检查是否有创新点描述
        content = str(proposal.get('content', ''))
        innovation_keywords = ["创新", "优化", "改进", "提升", "先进"]
        
        has_innovation = any(kw in content for kw in innovation_keywords)
        score = 80.0 if has_innovation else 50.0
        
        return CheckResult(
            check_id="soft_04",
            check_name="创新性评估",
            check_level=CheckLevel.MINOR,
            status=CheckStatus.PASS if has_innovation else CheckStatus.INFO,
            message="包含创新点描述" if has_innovation else "未发现明显创新点",
            score=score
        )


# ========== 知识图谱验证器 ==========

class OntologyValidator:
    """
    知识图谱验证器
    检查逻辑链的完整性和一致性
    """
    
    def __init__(self, ontology_manager: OntologyManager):
        self.ontology = ontology_manager
        logger.info("OntologyValidator initialized")
    
    async def validate_chain(self, proposal: Dict[str, Any]) -> List[CheckResult]:
        """
        验证逻辑链
        
        Args:
            proposal: 投标文件
            
        Returns:
            检查结果列表
        """
        results = []
        
        # 获取proposal关联的约束节点ID列表
        constraint_ids = proposal.get("constraint_ids", [])
        
        for constraint_id in constraint_ids:
            # 验证每个约束的依赖链
            validation = await self.ontology.validate_requirements_chain(UUID(constraint_id))
            
            status = CheckStatus.PASS if validation['is_valid'] else CheckStatus.FAIL
            
            result = CheckResult(
                check_id=f"kg_{constraint_id[:8]}",
                check_name="依赖链验证",
                check_level=CheckLevel.CRITICAL,
                status=status,
                message=f"依赖项{validation['dependency_count']}个，冲突{validation['conflict_count']}个",
                details=validation,
                score=100.0 if validation['is_valid'] else 0.0
            )
            results.append(result)
        
        logger.info(f"KG validation completed: {len(results)} chains checked")
        return results


# ========== 多代理评估器 ==========

class MultiAgentEvaluator:
    """
    多代理评估器 - 三层检查架构
    
    架构：
    Layer 1: 硬约束检查（确定性规则）
    Layer 2: 软约束检查（LLM语义评分）
    Layer 3: 知识图谱验证（逻辑链检查）
    """
    
    def __init__(self, ontology_manager: OntologyManager):
        """初始化评估器"""
        self.hard_checker = HardConstraintChecker()
        self.soft_checker = SoftConstraintChecker()
        self.kg_validator = OntologyValidator(ontology_manager)
        
        logger.info("MultiAgentEvaluator initialized with 3-layer architecture")
    
    async def evaluate(
        self, 
        proposal: Dict[str, Any], 
        tender: Dict[str, Any]
    ) -> EvaluationReport:
        """
        执行三层评估
        
        Args:
            proposal: 投标文件
            tender: 招标文件
            
        Returns:
            评估报告
        """
        logger.info(f"Starting evaluation: proposal={proposal.get('id')}, tender={tender.get('id')}")
        
        # Layer 1: 硬约束检查
        hard_results = await self.hard_checker.check(proposal, tender)
        
        # Layer 2: 软约束检查
        soft_results = await self.soft_checker.check(proposal, tender)
        
        # Layer 3: 知识图谱验证
        kg_results = await self.kg_validator.validate_chain(proposal)
        
        # 计算总分
        all_results = hard_results + soft_results + kg_results
        total_score = sum([r.score for r in all_results if r.score is not None])
        overall_score = total_score / len(all_results) if all_results else 0
        
        # 判断总体状态
        has_critical_fail = any(
            r.status == CheckStatus.FAIL and r.check_level == CheckLevel.CRITICAL
            for r in all_results
        )
        overall_status = CheckStatus.FAIL if has_critical_fail else CheckStatus.PASS
        
        # 生成建议
        recommendations = self._generate_recommendations(hard_results, soft_results, kg_results)
        
        report = EvaluationReport(
            proposal_id=str(proposal.get('id', 'unknown')),
            tender_id=str(tender.get('id', 'unknown')),
            hard_constraint_results=hard_results,
            soft_constraint_results=soft_results,
            kg_validation_results=kg_results,
            overall_score=overall_score,
            overall_status=overall_status,
            recommendations=recommendations,
            created_at=str(datetime.now())
        )
        
        logger.info(
            f"Evaluation completed: score={overall_score:.1f}, status={overall_status.value}"
        )
        
        return report
    
    def _generate_recommendations(
        self,
        hard_results: List[CheckResult],
        soft_results: List[CheckResult],
        kg_results: List[CheckResult]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 硬约束失败项
        for result in hard_results:
            if result.status == CheckStatus.FAIL:
                recommendations.append(f"【关键】{result.check_name}：{result.message}")
        
        # 软约束警告项
        for result in soft_results:
            if result.status == CheckStatus.WARNING:
                recommendations.append(f"【建议】{result.check_name}：{result.message}")
        
        # 知识图谱问题
        for result in kg_results:
            if not result.details.get('is_valid'):
                recommendations.append(f"【逻辑】存在依赖冲突或缺失证据")
        
        return recommendations
