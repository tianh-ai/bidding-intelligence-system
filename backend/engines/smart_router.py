"""
智能路由器（Smart Router）
实现85/10/5分流策略：85% KB检索 + 10% LLM微调 + 5% LLM生成
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum
import openai

from core.logger import logger
from core.config import settings
from core.cache import cache, cache_result


# ========== 内容来源枚举 ==========

class ContentSource(str, Enum):
    """内容来源"""
    KB_EXACT_MATCH = "kb_exact_match"      # KB精确匹配（85%）
    LLM_ADAPT = "llm_adapt"                # LLM微调（10%）
    LLM_GENERATE = "llm_generate"          # LLM生成（5%）


# ========== Pydantic模型 ==========

class RequirementNode(BaseModel):
    """需求节点"""
    requirement_id: str
    title: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None  # 向量嵌入


class RoutingDecision(BaseModel):
    """路由决策"""
    requirement_id: str
    source: ContentSource
    similarity_score: float
    content: str
    reasoning: str  # 决策理由
    cost_estimate: float  # 预估成本（美元）


class RoutingStats(BaseModel):
    """路由统计"""
    total_requests: int
    kb_exact_match_count: int
    llm_adapt_count: int
    llm_generate_count: int
    average_similarity: float
    total_cost: float
    
    @property
    def kb_percentage(self) -> float:
        return (self.kb_exact_match_count / self.total_requests * 100) if self.total_requests > 0 else 0
    
    @property
    def llm_adapt_percentage(self) -> float:
        return (self.llm_adapt_count / self.total_requests * 100) if self.total_requests > 0 else 0
    
    @property
    def llm_generate_percentage(self) -> float:
        return (self.llm_generate_count / self.total_requests * 100) if self.total_requests > 0 else 0


# ========== 智能路由器 ==========

class SmartRouter:
    """
    智能路由器 - 85/10/5分流策略
    
    核心功能：
    1. 计算需求与知识库的相似度
    2. 根据相似度分流到不同处理路径
    3. 成本优化（减少LLM调用）
    4. 性能监控
    
    分流规则：
    - similarity > 0.8  → KB精确匹配（85%目标）
    - 0.5 < similarity ≤ 0.8 → LLM微调（10%目标）
    - similarity ≤ 0.5  → LLM生成（5%目标）
    """
    
    def __init__(self, db_connection):
        """
        初始化智能路由器
        
        Args:
            db_connection: 数据库连接
        """
        self.db = db_connection
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 阈值配置（可动态调整）
        self.KB_THRESHOLD = 0.8      # KB精确匹配阈值
        self.ADAPT_THRESHOLD = 0.5   # LLM微调阈值
    
    def update_thresholds(self, kb_threshold: Optional[float] = None, adapt_threshold: Optional[float] = None):
        """
        更新路由阈值（用于反馈闭环优化）
        
        Args:
            kb_threshold: 新的KB匹配阈值
            adapt_threshold: 新的LLM微调阈值
        """
        if kb_threshold is not None:
            old_kb = self.KB_THRESHOLD
            self.KB_THRESHOLD = max(0.5, min(0.95, kb_threshold))  # 限制在0.5-0.95
            logger.info(f"SmartRouter threshold updated: KB {old_kb:.2f} -> {self.KB_THRESHOLD:.2f}")
        
        if adapt_threshold is not None:
            old_adapt = self.ADAPT_THRESHOLD
            self.ADAPT_THRESHOLD = max(0.3, min(0.7, adapt_threshold))  # 限制在0.3-0.7
            logger.info(f"SmartRouter threshold updated: ADAPT {old_adapt:.2f} -> {self.ADAPT_THRESHOLD:.2f}")
        
        # 成本配置（美元/1000 tokens）
        self.COST_PER_1K_TOKENS = 0.03
        
        # 统计数据
        self.stats = RoutingStats(
            total_requests=0,
            kb_exact_match_count=0,
            llm_adapt_count=0,
            llm_generate_count=0,
            average_similarity=0.0,
            total_cost=0.0
        )
        
        logger.info("SmartRouter initialized with 85/10/5 strategy")
    
    # ========== 核心路由方法 ==========
    
    async def route_content(
        self, 
        requirement: RequirementNode
    ) -> RoutingDecision:
        """
        智能路由决策
        
        Args:
            requirement: 需求节点
            
        Returns:
            路由决策
        """
        logger.info(f"Routing requirement: {requirement.requirement_id}")
        
        # 1. 计算相似度
        similarity = await self._calculate_kb_similarity(requirement)
        
        # 2. 根据相似度分流
        if similarity > self.KB_THRESHOLD:
            # 85% - KB精确匹配
            decision = await self._kb_exact_match(requirement, similarity)
            self.stats.kb_exact_match_count += 1
            
        elif similarity > self.ADAPT_THRESHOLD:
            # 10% - LLM微调
            decision = await self._llm_adapt(requirement, similarity)
            self.stats.llm_adapt_count += 1
            
        else:
            # 5% - LLM生成
            decision = await self._llm_generate(requirement, similarity)
            self.stats.llm_generate_count += 1
        
        # 3. 更新统计
        self.stats.total_requests += 1
        self.stats.average_similarity = (
            (self.stats.average_similarity * (self.stats.total_requests - 1) + similarity)
            / self.stats.total_requests
        )
        self.stats.total_cost += decision.cost_estimate
        
        logger.info(
            f"Routing decision: {decision.source.value} (similarity={similarity:.2f})"
        )
        
        return decision
    
    @cache_result(prefix="kb_similarity", ttl=3600)
    async def _calculate_kb_similarity(self, requirement: RequirementNode) -> float:
        """
        计算需求与知识库的相似度
        使用pgvector进行向量检索
        
        Args:
            requirement: 需求节点
            
        Returns:
            相似度分数（0-1）
        """
        # 1. 获取需求的向量嵌入
        if not requirement.embedding:
            requirement.embedding = await self._get_embedding(requirement.description)
        
        # 2. 在知识库中检索最相似的内容
        query = """
            SELECT 
                id,
                content,
                1 - (embedding <=> $1::vector) as similarity
            FROM kb_templates
            WHERE 1 - (embedding <=> $1::vector) > 0.3
            ORDER BY embedding <=> $1::vector
            LIMIT 1
        """
        
        result = await self.db.fetchrow(query, requirement.embedding)
        
        if result:
            similarity = float(result['similarity'])
            logger.debug(f"KB similarity: {similarity:.4f}")
            return similarity
        
        return 0.0
    
    # ========== 三种处理路径 ==========
    
    async def _kb_exact_match(
        self, 
        requirement: RequirementNode, 
        similarity: float
    ) -> RoutingDecision:
        """
        路径1：KB精确匹配（85%）
        直接从知识库检索，无需LLM
        """
        logger.info(f"Using KB exact match for {requirement.requirement_id}")
        
        # 从知识库检索
        query = """
            SELECT content, metadata
            FROM kb_templates
            WHERE 1 - (embedding <=> $1::vector) > $2
            ORDER BY embedding <=> $1::vector
            LIMIT 1
        """
        
        result = await self.db.fetchrow(
            query, 
            requirement.embedding, 
            self.KB_THRESHOLD
        )
        
        content = result['content'] if result else "未找到匹配内容"
        
        return RoutingDecision(
            requirement_id=requirement.requirement_id,
            source=ContentSource.KB_EXACT_MATCH,
            similarity_score=similarity,
            content=content,
            reasoning=f"相似度{similarity:.2f}超过阈值{self.KB_THRESHOLD}，直接使用KB内容",
            cost_estimate=0.0  # KB检索无成本
        )
    
    async def _llm_adapt(
        self, 
        requirement: RequirementNode, 
        similarity: float
    ) -> RoutingDecision:
        """
        路径2：LLM微调（10%）
        检索KB内容，使用LLM进行轻度改写
        """
        logger.info(f"Using LLM adapt for {requirement.requirement_id}")
        
        # 1. 检索KB内容
        query = """
            SELECT content
            FROM kb_templates
            WHERE 1 - (embedding <=> $1::vector) > $2
            ORDER BY embedding <=> $1::vector
            LIMIT 1
        """
        
        result = await self.db.fetchrow(
            query, 
            requirement.embedding, 
            self.ADAPT_THRESHOLD
        )
        
        kb_content = result['content'] if result else ""
        
        # 2. LLM微调
        prompt = f"""
请根据以下参考内容，微调改写以满足新的需求：

**参考内容**：
{kb_content}

**新需求**：
{requirement.description}

**要求**：
1. 保持核心结构和逻辑
2. 调整细节以匹配新需求
3. 保持专业性和准确性
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "你是投标文件改写专家"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        adapted_content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        cost = (tokens_used / 1000) * self.COST_PER_1K_TOKENS
        
        return RoutingDecision(
            requirement_id=requirement.requirement_id,
            source=ContentSource.LLM_ADAPT,
            similarity_score=similarity,
            content=adapted_content,
            reasoning=f"相似度{similarity:.2f}在范围内，使用LLM微调KB内容",
            cost_estimate=cost
        )
    
    async def _llm_generate(
        self, 
        requirement: RequirementNode, 
        similarity: float
    ) -> RoutingDecision:
        """
        路径3：LLM生成（5%）
        完全由LLM生成新内容
        """
        logger.info(f"Using LLM generate for {requirement.requirement_id}")
        
        prompt = f"""
请根据以下需求生成完整的投标文件内容：

**需求标题**：
{requirement.title}

**需求描述**：
{requirement.description}

**关键词**：
{', '.join(requirement.keywords)}

**要求**：
1. 内容完整、专业
2. 逻辑清晰、结构合理
3. 符合投标文件规范
4. 字数不少于500字
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "你是资深投标文件撰写专家，擅长生成高质量投标内容"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.5
        )
        
        generated_content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        cost = (tokens_used / 1000) * self.COST_PER_1K_TOKENS
        
        return RoutingDecision(
            requirement_id=requirement.requirement_id,
            source=ContentSource.LLM_GENERATE,
            similarity_score=similarity,
            content=generated_content,
            reasoning=f"相似度{similarity:.2f}过低，使用LLM全新生成",
            cost_estimate=cost
        )
    
    # ========== 辅助方法 ==========
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入
        使用OpenAI Embedding API
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        return response.data[0].embedding
    
    # ========== 统计与监控 ==========
    
    def get_stats(self) -> RoutingStats:
        """获取路由统计数据"""
        return self.stats
    
    def reset_stats(self):
        """重置统计数据"""
        self.stats = RoutingStats(
            total_requests=0,
            kb_exact_match_count=0,
            llm_adapt_count=0,
            llm_generate_count=0,
            average_similarity=0.0,
            total_cost=0.0
        )
        logger.info("Routing stats reset")
    
    async def analyze_routing_efficiency(self) -> Dict[str, Any]:
        """
        分析路由效率
        
        Returns:
            效率分析报告
        """
        stats = self.get_stats()
        
        # 计算成本节约（与全部LLM生成对比）
        if stats.total_requests > 0:
            # 假设全部LLM生成的成本
            full_llm_cost = stats.total_requests * 0.05  # 平均每次$0.05
            cost_saved = full_llm_cost - stats.total_cost
            cost_saved_percentage = (cost_saved / full_llm_cost * 100) if full_llm_cost > 0 else 0
        else:
            cost_saved = 0
            cost_saved_percentage = 0
        
        return {
            "total_requests": stats.total_requests,
            "distribution": {
                "kb_exact_match": f"{stats.kb_percentage:.1f}%",
                "llm_adapt": f"{stats.llm_adapt_percentage:.1f}%",
                "llm_generate": f"{stats.llm_generate_percentage:.1f}%"
            },
            "average_similarity": f"{stats.average_similarity:.4f}",
            "cost_analysis": {
                "actual_cost": f"${stats.total_cost:.2f}",
                "full_llm_cost_estimate": f"${stats.total_requests * 0.05:.2f}",
                "cost_saved": f"${cost_saved:.2f}",
                "cost_saved_percentage": f"{cost_saved_percentage:.1f}%"
            },
            "target_vs_actual": {
                "kb_target": "85%",
                "kb_actual": f"{stats.kb_percentage:.1f}%",
                "kb_delta": f"{stats.kb_percentage - 85:.1f}%"
            }
        }
