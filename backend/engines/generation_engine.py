"""
生成引擎 (Generation Engine)
基于约束和逻辑规则生成投标文案
支持多版本生成、对比、质量评分
"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from core.logger import logger
from core.llm_router import get_llm_router, TaskType


class GenerationStrategy(str, Enum):
    """生成策略"""
    CONSERVATIVE = "conservative"  # 保守策略（优先匹配现有方案）
    BALANCED = "balanced"  # 平衡策略（混合生成）
    CREATIVE = "creative"  # 创意策略（鼓励新内容）


class GenerationMode(str, Enum):
    """生成模式"""
    FULL = "full"  # 全文生成
    PARTIAL = "partial"  # 部分生成
    INCREMENTAL = "incremental"  # 增量生成


class GeneratedContent(BaseModel):
    """生成的内容"""
    content_id: str = Field(..., description="内容ID")
    chapter_id: str = Field(..., description="章节ID")
    content: str = Field(..., description="生成的文案")
    source: str = Field(..., description="内容来源：KB/LLM_ADAPT/LLM_GENERATE")
    confidence: float = Field(..., ge=0, le=100, description="生成信心度 0-100")
    tokens_used: int = Field(..., description="使用的 token 数")
    generation_time: float = Field(..., description="生成耗时（秒）")
    related_constraints: List[str] = Field(default_factory=list, description="相关约束列表")


class GenerationVersion(BaseModel):
    """生成版本"""
    version_id: str = Field(..., description="版本ID")
    proposal_id: str = Field(..., description="投标书ID")
    tender_id: str = Field(..., description="招标书ID")
    strategy: GenerationStrategy = Field(..., description="生成策略")
    mode: GenerationMode = Field(..., description="生成模式")
    contents: List[GeneratedContent] = Field(..., description="生成内容列表")
    overall_score: float = Field(..., ge=0, le=100, description="总体评分")
    generated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict = Field(default_factory=dict, description="元数据")


class GenerationQualityMetrics(BaseModel):
    """生成质量指标"""
    fluency_score: float = Field(..., ge=0, le=100, description="流畅度评分")
    relevance_score: float = Field(..., ge=0, le=100, description="相关性评分")
    constraint_compliance: float = Field(..., ge=0, le=100, description="约束符合度")
    coverage_score: float = Field(..., ge=0, le=100, description="覆盖度评分")
    originality_score: float = Field(..., ge=0, le=100, description="原创度评分")
    overall_score: float = Field(..., ge=0, le=100, description="总体评分")


class GenerationEngine:
    """
    智能生成引擎
    
    功能：
    - 基于约束和规则生成投标文案
    - 支持多版本生成
    - 版本对比与质量评分
    - 生成过程可追溯
    """
    
    def __init__(self):
        """初始化生成引擎"""
        logger.info("GenerationEngine initialized")
        self.generation_history: List[GenerationVersion] = []
        self.content_cache: Dict[str, str] = {}
        self.llm_router = get_llm_router()  # 获取LLM路由器
        logger.info("LLM Router integrated into GenerationEngine")
        self.llm_router = get_llm_router()  # 获取LLM路由器
        
    async def generate_proposal(
        self,
        tender_id: str,
        template_id: str,
        strategy: GenerationStrategy = GenerationStrategy.BALANCED,
        mode: GenerationMode = GenerationMode.FULL,
        options: Optional[Dict] = None
    ) -> GenerationVersion:
        """
        生成投标书
        
        Args:
            tender_id: 招标书ID
            template_id: 模板ID
            strategy: 生成策略
            mode: 生成模式
            options: 额外选项
            
        Returns:
            生成的版本对象
        """
        logger.info(
            f"Starting proposal generation",
            extra={
                "tender_id": tender_id,
                "template_id": template_id,
                "strategy": strategy.value,
                "mode": mode.value
            }
        )
        
        version_id = f"gen_{tender_id}_{datetime.now().timestamp()}"
        contents: List[GeneratedContent] = []
        
        # 模拟生成过程（实际实现需要集成 LLM 和知识库）
        if mode == GenerationMode.FULL:
            # 全文生成：遍历所有章节
            contents = await self._generate_all_chapters(
                tender_id, template_id, strategy
            )
        elif mode == GenerationMode.PARTIAL:
            # 部分生成：生成指定章节
            chapter_ids = options.get("chapter_ids", []) if options else []
            contents = await self._generate_specific_chapters(
                tender_id, template_id, strategy, chapter_ids
            )
        else:  # INCREMENTAL
            # 增量生成：基于现有内容扩展
            proposal_id = options.get("proposal_id", "") if options else ""
            contents = await self._generate_incremental(
                tender_id, template_id, strategy, proposal_id
            )
        
        # 计算总体评分
        quality_metrics = await self._calculate_quality_metrics(contents)
        overall_score = quality_metrics.overall_score
        
        # 创建版本对象
        version = GenerationVersion(
            version_id=version_id,
            proposal_id=f"prop_{tender_id}_{datetime.now().timestamp()}",
            tender_id=tender_id,
            strategy=strategy,
            mode=mode,
            contents=contents,
            overall_score=overall_score,
            metadata={
                "template_id": template_id,
                "quality_metrics": quality_metrics.dict(),
                "generation_options": options or {}
            }
        )
        
        # 保存到历史
        self.generation_history.append(version)
        
        logger.info(
            f"Proposal generation completed",
            extra={
                "version_id": version_id,
                "content_count": len(contents),
                "overall_score": overall_score,
                "total_tokens": sum(c.tokens_used for c in contents)
            }
        )
        
        return version
    
    async def _generate_all_chapters(
        self,
        tender_id: str,
        template_id: str,
        strategy: GenerationStrategy
    ) -> List[GeneratedContent]:
        """生成所有章节"""
        contents = []
        
        # 模拟章节数据（实际实现需要从数据库读取）
        chapter_ids = [f"ch_{i}" for i in range(1, 6)]
        
        for chapter_id in chapter_ids:
            content = await self._generate_single_content(
                tender_id, template_id, chapter_id, strategy
            )
            if content:
                contents.append(content)
        
        return contents
    
    async def _generate_specific_chapters(
        self,
        tender_id: str,
        template_id: str,
        strategy: GenerationStrategy,
        chapter_ids: List[str]
    ) -> List[GeneratedContent]:
        """生成指定章节"""
        contents = []
        
        for chapter_id in chapter_ids:
            content = await self._generate_single_content(
                tender_id, template_id, chapter_id, strategy
            )
            if content:
                contents.append(content)
        
        return contents
    
    async def _generate_incremental(
        self,
        tender_id: str,
        template_id: str,
        strategy: GenerationStrategy,
        proposal_id: str
    ) -> List[GeneratedContent]:
        """增量生成（基于现有投标书扩展）"""
        # 实际实现需要：
        # 1. 读取现有投标书内容
        # 2. 识别可改进的章节
        # 3. 生成改进版本
        # 4. 与原版本对比
        
        contents = []
        logger.info(
            f"Incremental generation for proposal {proposal_id}",
            extra={"tender_id": tender_id}
        )
        
        return contents
    
    async def _generate_single_content(
        self,
        tender_id: str,
        template_id: str,
        chapter_id: str,
        strategy: GenerationStrategy
    ) -> Optional[GeneratedContent]:
        """生成单个内容块"""
        import asyncio
        import time
        
        start_time = time.time()
        
        # 根据策略选择生成源和置信度
        if strategy == GenerationStrategy.CONSERVATIVE:
            source = "KB"
            confidence = 85.0
        elif strategy == GenerationStrategy.CREATIVE:
            source = "LLM_GENERATE"
            confidence = 65.0
        else:  # BALANCED
            source = "LLM_ADAPT"
            confidence = 75.0
        
        # 使用LLM生成真实内容
        try:
            generated_text = await self._generate_with_llm(chapter_id, strategy)
        except:
            # 降级到模板
            generated_text = self._generate_mock_text(chapter_id)
            confidence -= 10  # 降低置信度
        
        elapsed = time.time() - start_time
        
        content = GeneratedContent(
            content_id=f"cnt_{chapter_id}_{datetime.now().timestamp()}",
            chapter_id=chapter_id,
            content=generated_text,
            source=source,
            confidence=confidence,
            tokens_used=150 + (50 if source == "LLM_GENERATE" else 0),
            generation_time=elapsed,
            related_constraints=[f"constraint_{i}" for i in range(1, 4)]
        )
        
        return content
    
    def _generate_mock_text(self, chapter_id: str) -> str:
        """生成模拟文本（实际实现使用 LLM）"""
        templates = {
            "ch_1": "项目概述：本投标书针对招标项目进行全面的技术方案设计...",
            "ch_2": "技术方案：采用先进的技术架构，满足所有技术要求...",
            "ch_3": "商务条款：价格具有竞争力，支付方式灵活...",
            "ch_4": "实施计划：分阶段实施，确保项目按时完成...",
            "ch_5": "团队资质：团队成员具备丰富的行业经验..."
        }
        return templates.get(chapter_id, f"第 {chapter_id} 章内容")
    
    async def _generate_with_llm(
        self,
        chapter_id: str,
        strategy: GenerationStrategy
    ) -> str:
        """使用LLM生成真实内容"""
        # 章节描述映射
        chapter_descriptions = {
            "ch_1": "项目概述 - 介绍项目背景、目标和价值",
            "ch_2": "技术方案 - 详细说明技术路线、架构设计和实施方法",
            "ch_3": "商务报价 - 项目预算、成本分析和报价说明",
            "ch_4": "实施计划 - 项目实施的时间安排、里程碑和交付物",
            "ch_5": "团队组成 - 项目团队成员、资质和经验介绍"
        }
        
        chapter_desc = chapter_descriptions.get(chapter_id, f"{chapter_id}章节内容")
        
        # 策略对应的系统提示
        system_prompts = {
            GenerationStrategy.CONSERVATIVE: "你是一位专业的投标文案撰写专家。请严格按照常规格式和要求，生成规范、稳健的投标文件内容。避免使用过于创新或冒险的表述。",
            GenerationStrategy.BALANCED: "你是一位经验丰富的投标文案专家。请在遵守规范的基础上，适当融入创新元素，生成既专业又有亮点的投标文件内容。",
            GenerationStrategy.CREATIVE: "你是一位富有创意的投标策划专家。请在保证专业性的前提下，大胆创新，提出独特的解决方案和亮点，使投标文件脱颖而出。"
        }
        
        # 构建用户提示词
        user_prompt = f"""请为投标文件生成【{chapter_desc}】的内容。

要求：
1. 内容专业、完整、有说服力
2. 字数控制在300-500字之间
3. 使用投标文件的正式语言风格
4. 突出我方的优势和特点
5. 避免空洞的套话，要有实质内容

请直接生成内容，不要包含额外的说明。"""
        
        try:
            # 使用DeepSeek生成内容
            content = await self.llm_router.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompts.get(strategy, system_prompts[GenerationStrategy.BALANCED]),
                task_type=TaskType.GENERATION,
                temperature=0.7 if strategy == GenerationStrategy.CREATIVE else 0.5,
                model_name="deepseek"  # 明确使用DeepSeek生成
            )
            
            logger.info(
                f"LLM generated content for {chapter_id}",
                extra={
                    "chapter": chapter_id,
                    "strategy": strategy.value,
                    "content_length": len(content),
                    "model": "deepseek"
                }
            )
            
            return content.strip()
            
        except Exception as e:
            logger.error(
                f"LLM generation failed, using template",
                extra={"chapter": chapter_id, "error": str(e)}
            )
            # 失败时使用模板
            return self._generate_mock_text(chapter_id)
    
    async def _calculate_quality_metrics(
        self,
        contents: List[GeneratedContent]
    ) -> GenerationQualityMetrics:
        """计算质量指标"""
        if not contents:
            return GenerationQualityMetrics(
                fluency_score=0, relevance_score=0, constraint_compliance=0,
                coverage_score=0, originality_score=0, overall_score=0
            )
        
        # 基于内容来源和信心度计算各项指标
        avg_confidence = sum(c.confidence for c in contents) / len(contents)
        llm_generate_count = sum(1 for c in contents if c.source == "LLM_GENERATE")
        
        fluency_score = min(100, avg_confidence + 5)
        relevance_score = min(100, avg_confidence)
        constraint_compliance = min(100, 90 + (llm_generate_count * 2))
        coverage_score = min(100, (len(contents) / 5) * 100)
        originality_score = min(100, (llm_generate_count / len(contents)) * 100)
        
        overall_score = (
            fluency_score * 0.2 +
            relevance_score * 0.2 +
            constraint_compliance * 0.3 +
            coverage_score * 0.15 +
            originality_score * 0.15
        )
        
        return GenerationQualityMetrics(
            fluency_score=fluency_score,
            relevance_score=relevance_score,
            constraint_compliance=constraint_compliance,
            coverage_score=coverage_score,
            originality_score=originality_score,
            overall_score=overall_score
        )
    
    async def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> Dict:
        """
        对比两个版本
        
        Args:
            version_id_1: 版本1 ID
            version_id_2: 版本2 ID
            
        Returns:
            对比结果
        """
        v1 = next((v for v in self.generation_history if v.version_id == version_id_1), None)
        v2 = next((v for v in self.generation_history if v.version_id == version_id_2), None)
        
        if not v1 or not v2:
            logger.error("Version not found for comparison")
            return {"error": "Version not found"}
        
        logger.info(
            f"Comparing versions {version_id_1} vs {version_id_2}",
            extra={"v1_score": v1.overall_score, "v2_score": v2.overall_score}
        )
        
        comparison = {
            "version_1": {
                "id": v1.version_id,
                "score": v1.overall_score,
                "strategy": v1.strategy.value,
                "content_count": len(v1.contents)
            },
            "version_2": {
                "id": v2.version_id,
                "score": v2.overall_score,
                "strategy": v2.strategy.value,
                "content_count": len(v2.contents)
            },
            "score_difference": v2.overall_score - v1.overall_score,
            "winner": "version_2" if v2.overall_score > v1.overall_score else "version_1",
            "recommendation": self._generate_recommendation(v1, v2)
        }
        
        return comparison
    
    def _generate_recommendation(
        self,
        v1: GenerationVersion,
        v2: GenerationVersion
    ) -> str:
        """生成推荐"""
        score_diff = v2.overall_score - v1.overall_score
        
        if abs(score_diff) < 2:
            return "两个版本质量相近，可根据内容风格选择"
        elif score_diff > 10:
            return "版本2显著优于版本1，建议采用版本2"
        else:
            return "版本2略优于版本1"
    
    async def get_generation_history(
        self,
        tender_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """获取生成历史"""
        history = self.generation_history
        
        if tender_id:
            history = [v for v in history if v.tender_id == tender_id]
        
        return [
            {
                "version_id": v.version_id,
                "tender_id": v.tender_id,
                "strategy": v.strategy.value,
                "overall_score": v.overall_score,
                "generated_at": v.generated_at.isoformat(),
                "content_count": len(v.contents)
            }
            for v in history[-limit:]
        ]

