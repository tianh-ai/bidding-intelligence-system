"""
Layer 2: 约束提取代理（Constraint Extractor Agent）
使用OpenAI Function Calling进行结构化约束提取
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum
import json
import openai

from core.logger import logger
from core.config import settings
from db.ontology import (
    OntologyManager, OntologyNode, OntologyRelation,
    NodeType, RelationType
)
from agents.preprocessor import TextBlock, TableBlock


# ========== 约束类型枚举 ==========

class ConstraintType(str, Enum):
    """约束类型"""
    MUST_HAVE = "must_have"              # 硬约束（必须满足）
    SHOULD_HAVE = "should_have"          # 软约束（应该满足）
    FORBIDDEN = "forbidden"              # 禁止项
    CONDITIONAL = "conditional"          # 条件约束
    SCORING = "scoring"                  # 评分规则


class ConstraintCategory(str, Enum):
    """约束分类"""
    QUALIFICATION = "qualification"      # 资质要求
    TECHNICAL = "technical"              # 技术要求
    COMMERCIAL = "commercial"            # 商务要求
    COMPLIANCE = "compliance"            # 合规要求
    PERFORMANCE = "performance"          # 性能要求


# ========== Pydantic模型 ==========

class ExtractedConstraint(BaseModel):
    """提取的约束"""
    constraint_id: str = Field(default_factory=lambda: str(uuid4()))
    constraint_type: ConstraintType
    category: ConstraintCategory
    title: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    evidence_required: List[str] = Field(default_factory=list)  # 需要的证据材料
    scoring_weight: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConstraintExtractionResult(BaseModel):
    """约束提取结果"""
    source_block_id: str
    constraints: List[ExtractedConstraint]
    ontology_nodes_created: List[UUID] = Field(default_factory=list)
    ontology_relations_created: List[UUID] = Field(default_factory=list)


# ========== 约束提取代理 ==========

class ConstraintExtractorAgent:
    """
    约束提取代理 - Layer 2
    
    核心功能：
    1. 使用OpenAI Function Calling提取约束
    2. 自动创建本体节点
    3. 建立约束-证据关系
    4. 识别约束类型和优先级
    """
    
    def __init__(self, ontology_manager: OntologyManager):
        """
        初始化约束提取代理
        
        Args:
            ontology_manager: 本体管理器实例
        """
        self.ontology = ontology_manager
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Function Calling Schema
        self.constraint_schema = {
            "name": "extract_constraint",
            "description": "从文本中提取投标文件的约束条件",
            "parameters": {
                "type": "object",
                "properties": {
                    "constraint_type": {
                        "type": "string",
                        "enum": ["must_have", "should_have", "forbidden", "conditional", "scoring"],
                        "description": "约束类型：must_have（硬约束）、should_have（软约束）、forbidden（禁止）、conditional（条件）、scoring（评分）"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["qualification", "technical", "commercial", "compliance", "performance"],
                        "description": "约束分类"
                    },
                    "title": {
                        "type": "string",
                        "description": "约束标题"
                    },
                    "description": {
                        "type": "string",
                        "description": "约束详细描述"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关键词列表"
                    },
                    "evidence_required": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "需要提供的证据材料列表"
                    },
                    "scoring_weight": {
                        "type": "number",
                        "description": "评分权重（0-100）"
                    }
                },
                "required": ["constraint_type", "category", "title", "description"]
            }
        }
        
        logger.info("ConstraintExtractorAgent initialized")
    
    # ========== 核心方法 ==========
    
    async def extract_constraints_from_text(
        self, 
        text: str,
        source_block_id: str = "unknown"
    ) -> ConstraintExtractionResult:
        """
        从文本块提取约束
        
        Args:
            text: 文本内容
            source_block_id: 来源文本块ID
            
        Returns:
            约束提取结果
        """
        logger.info(f"Extracting constraints from block: {source_block_id}")
        
        # 调用OpenAI Function Calling
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是投标文件分析专家，负责从招标文件中提取约束条件。请识别所有硬约束、软约束、禁止项、评分规则等。"
                    },
                    {
                        "role": "user",
                        "content": f"请从以下文本中提取所有约束条件：\n\n{text}"
                    }
                ],
                functions=[self.constraint_schema],
                function_call={"name": "extract_constraint"}
            )
            
            # 解析结果
            function_call = response.choices[0].message.function_call
            if function_call:
                constraint_data = json.loads(function_call.arguments)
                constraint = ExtractedConstraint(**constraint_data)
                
                # 创建本体节点和关系
                node_ids, relation_ids = await self._create_ontology_from_constraint(constraint)
                
                return ConstraintExtractionResult(
                    source_block_id=source_block_id,
                    constraints=[constraint],
                    ontology_nodes_created=node_ids,
                    ontology_relations_created=relation_ids
                )
            
        except Exception as e:
            logger.error(f"Failed to extract constraints: {e}")
            # 降级：使用规则提取
            return await self._fallback_rule_based_extraction(text, source_block_id)
        
        return ConstraintExtractionResult(
            source_block_id=source_block_id,
            constraints=[]
        )
    
    async def extract_constraints_from_table(
        self, 
        table: TableBlock
    ) -> ConstraintExtractionResult:
        """
        从表格提取约束（通常是评分规则、技术参数表）
        
        Args:
            table: 表格块
            
        Returns:
            约束提取结果
        """
        logger.info(f"Extracting constraints from table: {table.table_id}")
        
        # 将Markdown表格转换为文本描述
        table_text = f"表格内容：\n{table.markdown_content}\n\n"
        table_text += f"表头：{', '.join(table.headers)}\n"
        table_text += f"行数：{table.row_count}，列数：{table.col_count}"
        
        return await self.extract_constraints_from_text(table_text, table.table_id)
    
    async def batch_extract_from_blocks(
        self, 
        text_blocks: List[TextBlock],
        table_blocks: List[TableBlock]
    ) -> List[ConstraintExtractionResult]:
        """
        批量提取约束
        
        Args:
            text_blocks: 文本块列表
            table_blocks: 表格块列表
            
        Returns:
            约束提取结果列表
        """
        results = []
        
        # 处理文本块
        for block in text_blocks:
            if block.block_type in ["paragraph", "list"]:
                result = await self.extract_constraints_from_text(
                    block.content, 
                    block.block_id
                )
                if result.constraints:
                    results.append(result)
        
        # 处理表格
        for table in table_blocks:
            result = await self.extract_constraints_from_table(table)
            if result.constraints:
                results.append(result)
        
        logger.info(f"Batch extraction completed: {len(results)} constraint groups found")
        return results
    
    async def _create_ontology_from_constraint(
        self, 
        constraint: ExtractedConstraint
    ) -> tuple[List[UUID], List[UUID]]:
        """
        从约束创建本体节点和关系
        
        Returns:
            (节点ID列表, 关系ID列表)
        """
        node_ids = []
        relation_ids = []
        
        # 1. 创建约束节点
        constraint_node = OntologyNode(
            node_type=NodeType.CONSTRAINT,
            name=constraint.title,
            description=constraint.description,
            properties={
                "constraint_type": constraint.constraint_type.value,
                "category": constraint.category.value,
                "keywords": constraint.keywords,
                "scoring_weight": constraint.scoring_weight
            }
        )
        
        constraint_node_id = await self.ontology.create_node(constraint_node)
        node_ids.append(constraint_node_id)
        
        # 2. 创建证据节点并建立关系
        for evidence_name in constraint.evidence_required:
            evidence_node = OntologyNode(
                node_type=NodeType.EVIDENCE,
                name=evidence_name,
                description=f"{constraint.title}所需的证据材料",
                properties={
                    "required_by": constraint.title
                }
            )
            
            evidence_node_id = await self.ontology.create_node(evidence_node)
            node_ids.append(evidence_node_id)
            
            # 建立 constraint -> requires -> evidence 关系
            relation = OntologyRelation(
                from_node_id=constraint_node_id,
                to_node_id=evidence_node_id,
                relation_type=RelationType.REQUIRES,
                weight=1.0 if constraint.constraint_type == ConstraintType.MUST_HAVE else 0.5
            )
            
            relation_id = await self.ontology.create_relation(relation)
            relation_ids.append(relation_id)
        
        logger.info(
            f"Created ontology: {len(node_ids)} nodes, {len(relation_ids)} relations"
        )
        return node_ids, relation_ids
    
    async def _fallback_rule_based_extraction(
        self, 
        text: str, 
        source_block_id: str
    ) -> ConstraintExtractionResult:
        """
        降级方案：基于规则的约束提取
        当OpenAI API失败时使用
        """
        logger.warning("Using fallback rule-based extraction")
        
        constraints = []
        
        # 检测硬约束关键词
        must_keywords = ["必须", "强制", "应当", "shall", "must"]
        if any(kw in text for kw in must_keywords):
            constraint = ExtractedConstraint(
                constraint_type=ConstraintType.MUST_HAVE,
                category=ConstraintCategory.COMPLIANCE,
                title="检测到硬性要求",
                description=text[:200],  # 截取前200字
                keywords=must_keywords
            )
            constraints.append(constraint)
        
        return ConstraintExtractionResult(
            source_block_id=source_block_id,
            constraints=constraints,
            ontology_nodes_created=[],
            ontology_relations_created=[]
        )
    
    # ========== 高级功能 ==========
    
    async def analyze_constraint_dependencies(
        self, 
        constraint_id: UUID
    ) -> Dict[str, Any]:
        """
        分析约束的依赖关系
        
        Args:
            constraint_id: 约束节点ID
            
        Returns:
            依赖分析结果
        """
        # 获取依赖链
        dep_chain = await self.ontology.find_dependency_chain(constraint_id)
        
        # 获取冲突
        conflicts = await self.ontology.find_conflicts(constraint_id)
        
        # 验证完整性
        validation = await self.ontology.validate_requirements_chain(constraint_id)
        
        return {
            "dependency_chain": dep_chain,
            "conflicts": conflicts,
            "validation": validation
        }
    
    async def find_similar_constraints(
        self, 
        constraint_id: UUID, 
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        查找相似约束（用于知识复用）
        
        Args:
            constraint_id: 约束节点ID
            threshold: 相似度阈值
            
        Returns:
            相似约束列表
        """
        return await self.ontology.find_similar_subgraphs(constraint_id, threshold)
