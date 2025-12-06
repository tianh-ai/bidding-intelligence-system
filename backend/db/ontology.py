"""
本体管理系统 - PostgreSQL轻量级知识图谱
实现投标文件的本体建模和关系管理
"""

from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from core.logger import logger


# ========== 本体节点类型 ==========

class NodeType(str, Enum):
    """本体节点类型枚举"""
    REQUIREMENT = "requirement"           # 招标要求
    QUALIFICATION = "qualification"       # 资质要求
    TECHNICAL_SPEC = "technical_spec"     # 技术规格
    PRICE_ITEM = "price_item"            # 价格项目
    EVIDENCE = "evidence"                # 证据材料
    SCORING_RULE = "scoring_rule"        # 评分规则
    TEMPLATE = "template"                # 模板内容
    CONSTRAINT = "constraint"            # 约束条件
    STRATEGY = "strategy"                # 应答策略


class RelationType(str, Enum):
    """关系类型枚举"""
    DEPENDS_ON = "depends_on"            # 依赖于
    SATISFIES = "satisfies"              # 满足
    REQUIRES = "requires"                # 需要
    CONFLICTS_WITH = "conflicts_with"    # 冲突
    RELATES_TO = "relates_to"            # 关联
    DERIVED_FROM = "derived_from"        # 派生自
    VALIDATES = "validates"              # 验证


# ========== Pydantic模型 ==========

class OntologyNode(BaseModel):
    """本体节点模型"""
    id: UUID = Field(default_factory=uuid4)
    node_type: NodeType
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class OntologyRelation(BaseModel):
    """本体关系模型"""
    id: UUID = Field(default_factory=uuid4)
    from_node_id: UUID
    to_node_id: UUID
    relation_type: RelationType
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)


class OntologyPath(BaseModel):
    """本体路径（图遍历结果）"""
    nodes: List[OntologyNode]
    relations: List[OntologyRelation]
    total_weight: float


# ========== 本体管理器 ==========

class OntologyManager:
    """
    本体管理器 - 管理知识图谱的节点和关系
    
    核心功能：
    1. 节点CRUD
    2. 关系CRUD
    3. 图遍历（递归CTE）
    4. 依赖分析
    5. 冲突检测
    """
    
    def __init__(self, db_connection):
        """
        初始化本体管理器
        
        Args:
            db_connection: 数据库连接（asyncpg或psycopg2）
        """
        self.db = db_connection
        logger.info("OntologyManager initialized")
    
    # ========== 节点操作 ==========
    
    async def create_node(self, node: OntologyNode) -> UUID:
        """
        创建本体节点
        
        Args:
            node: 节点对象
            
        Returns:
            节点ID
        """
        query = """
            INSERT INTO ontology_nodes (id, node_type, name, description, properties, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        result = await self.db.fetchval(
            query,
            node.id,
            node.node_type.value,
            node.name,
            node.description,
            node.properties,
            node.created_at,
            node.updated_at
        )
        
        logger.info(f"Created ontology node: {node.id} ({node.node_type})")
        return result
    
    async def get_node(self, node_id: UUID) -> Optional[OntologyNode]:
        """获取节点"""
        query = """
            SELECT id, node_type, name, description, properties, created_at, updated_at
            FROM ontology_nodes
            WHERE id = $1
        """
        
        row = await self.db.fetchrow(query, node_id)
        
        if row:
            return OntologyNode(**dict(row))
        return None
    
    async def update_node(self, node_id: UUID, updates: Dict[str, Any]) -> bool:
        """更新节点属性"""
        # 构建动态UPDATE语句
        set_clauses = []
        params = []
        param_index = 1
        
        for key, value in updates.items():
            if key in ['name', 'description', 'properties']:
                set_clauses.append(f"{key} = ${param_index}")
                params.append(value)
                param_index += 1
        
        # 始终更新updated_at
        set_clauses.append(f"updated_at = ${param_index}")
        params.append(datetime.now())
        param_index += 1
        
        params.append(node_id)
        
        query = f"""
            UPDATE ontology_nodes
            SET {', '.join(set_clauses)}
            WHERE id = ${param_index}
        """
        
        await self.db.execute(query, *params)
        logger.info(f"Updated ontology node: {node_id}")
        return True
    
    async def delete_node(self, node_id: UUID) -> bool:
        """删除节点（级联删除关系）"""
        query = "DELETE FROM ontology_nodes WHERE id = $1"
        await self.db.execute(query, node_id)
        logger.info(f"Deleted ontology node: {node_id}")
        return True
    
    # ========== 关系操作 ==========
    
    async def create_relation(self, relation: OntologyRelation) -> UUID:
        """创建关系"""
        query = """
            INSERT INTO ontology_relations 
            (id, from_node_id, to_node_id, relation_type, properties, weight, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        result = await self.db.fetchval(
            query,
            relation.id,
            relation.from_node_id,
            relation.to_node_id,
            relation.relation_type.value,
            relation.properties,
            relation.weight,
            relation.created_at
        )
        
        logger.info(
            f"Created relation: {relation.from_node_id} -{relation.relation_type}-> {relation.to_node_id}"
        )
        return result
    
    async def get_node_relations(
        self, 
        node_id: UUID, 
        direction: str = "both"
    ) -> List[OntologyRelation]:
        """
        获取节点的所有关系
        
        Args:
            node_id: 节点ID
            direction: 方向（outgoing/incoming/both）
            
        Returns:
            关系列表
        """
        if direction == "outgoing":
            where_clause = "from_node_id = $1"
        elif direction == "incoming":
            where_clause = "to_node_id = $1"
        else:
            where_clause = "(from_node_id = $1 OR to_node_id = $1)"
        
        query = f"""
            SELECT id, from_node_id, to_node_id, relation_type, properties, weight, created_at
            FROM ontology_relations
            WHERE {where_clause}
        """
        
        rows = await self.db.fetch(query, node_id)
        return [OntologyRelation(**dict(row)) for row in rows]
    
    # ========== 图遍历 ==========
    
    async def find_dependency_chain(
        self, 
        node_id: UUID, 
        max_depth: int = 5
    ) -> OntologyPath:
        """
        查找依赖链（使用递归CTE）
        
        Args:
            node_id: 起始节点ID
            max_depth: 最大深度
            
        Returns:
            依赖路径
        """
        query = """
            WITH RECURSIVE dep_chain AS (
                -- 基础查询：起始节点
                SELECT 
                    n.id, n.node_type, n.name, n.description, n.properties,
                    NULL::UUID as from_id,
                    NULL::TEXT as relation_type,
                    0 as depth,
                    ARRAY[n.id] as path,
                    0.0 as accumulated_weight
                FROM ontology_nodes n
                WHERE n.id = $1
                
                UNION ALL
                
                -- 递归查询：沿着依赖关系前进
                SELECT 
                    n.id, n.node_type, n.name, n.description, n.properties,
                    dc.id as from_id,
                    r.relation_type,
                    dc.depth + 1,
                    dc.path || n.id,
                    dc.accumulated_weight + r.weight
                FROM ontology_nodes n
                JOIN ontology_relations r ON r.to_node_id = n.id
                JOIN dep_chain dc ON r.from_node_id = dc.id
                WHERE 
                    dc.depth < $2
                    AND NOT (n.id = ANY(dc.path))  -- 避免循环
                    AND r.relation_type IN ('depends_on', 'requires')
            )
            SELECT * FROM dep_chain
            ORDER BY depth, accumulated_weight DESC
        """
        
        rows = await self.db.fetch(query, node_id, max_depth)
        
        # 构建路径对象
        nodes = []
        relations = []
        total_weight = 0.0
        
        for row in rows:
            node = OntologyNode(
                id=row['id'],
                node_type=row['node_type'],
                name=row['name'],
                description=row['description'],
                properties=row['properties']
            )
            nodes.append(node)
            
            if row['from_id']:
                # 获取关系详情
                rel = await self.db.fetchrow(
                    "SELECT * FROM ontology_relations WHERE from_node_id = $1 AND to_node_id = $2",
                    row['from_id'],
                    row['id']
                )
                if rel:
                    relations.append(OntologyRelation(**dict(rel)))
                    total_weight += rel['weight']
        
        return OntologyPath(nodes=nodes, relations=relations, total_weight=total_weight)
    
    async def find_conflicts(self, node_id: UUID) -> List[OntologyNode]:
        """
        查找冲突节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            冲突节点列表
        """
        query = """
            SELECT n.*
            FROM ontology_nodes n
            JOIN ontology_relations r ON (
                (r.from_node_id = $1 AND r.to_node_id = n.id)
                OR
                (r.to_node_id = $1 AND r.from_node_id = n.id)
            )
            WHERE r.relation_type = 'conflicts_with'
        """
        
        rows = await self.db.fetch(query, node_id)
        return [OntologyNode(**dict(row)) for row in rows]
    
    async def validate_requirements_chain(
        self, 
        requirement_id: UUID
    ) -> Dict[str, Any]:
        """
        验证需求链的完整性
        
        检查：
        1. 所有依赖是否满足
        2. 是否存在冲突
        3. 证据是否充分
        
        Returns:
            验证结果
        """
        # 获取依赖链
        dep_chain = await self.find_dependency_chain(requirement_id)
        
        # 检查冲突
        conflicts = await self.find_conflicts(requirement_id)
        
        # 检查证据
        evidence_nodes = [n for n in dep_chain.nodes if n.node_type == NodeType.EVIDENCE]
        
        return {
            "is_valid": len(conflicts) == 0,
            "dependency_count": len(dep_chain.nodes),
            "conflict_count": len(conflicts),
            "evidence_count": len(evidence_nodes),
            "total_weight": dep_chain.total_weight,
            "conflicts": [{"id": str(c.id), "name": c.name} for c in conflicts],
            "missing_evidence": len(evidence_nodes) == 0
        }
    
    # ========== 高级查询 ==========
    
    async def find_similar_subgraphs(
        self, 
        node_id: UUID, 
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        查找相似的子图（用于知识复用）
        
        基于：
        1. 节点类型相似度
        2. 关系结构相似度
        3. 属性相似度
        
        Returns:
            相似子图列表
        """
        # 获取当前节点的邻居结构
        current_structure = await self._get_node_structure(node_id)
        
        # 查找所有相同类型的节点
        query = """
            SELECT id, node_type, name, properties
            FROM ontology_nodes
            WHERE node_type = $1 AND id != $2
        """
        
        current_node = await self.get_node(node_id)
        candidates = await self.db.fetch(query, current_node.node_type.value, node_id)
        
        similar_graphs = []
        
        for candidate in candidates:
            # 获取候选节点的结构
            candidate_structure = await self._get_node_structure(candidate['id'])
            
            # 计算结构相似度
            similarity = self._calculate_structure_similarity(
                current_structure,
                candidate_structure
            )
            
            if similarity >= similarity_threshold:
                similar_graphs.append({
                    "node_id": candidate['id'],
                    "name": candidate['name'],
                    "similarity": similarity,
                    "structure": candidate_structure
                })
        
        # 按相似度排序
        similar_graphs.sort(key=lambda x: x['similarity'], reverse=True)
        
        logger.info(f"Found {len(similar_graphs)} similar subgraphs for node {node_id}")
        return similar_graphs
    
    async def _get_node_structure(self, node_id: UUID) -> Dict[str, Any]:
        """获取节点的局部结构（邻居+关系）"""
        relations = await self.get_node_relations(node_id)
        
        structure = {
            "outgoing_count": len([r for r in relations if r.from_node_id == node_id]),
            "incoming_count": len([r for r in relations if r.to_node_id == node_id]),
            "relation_types": list(set([r.relation_type.value for r in relations])),
            "total_weight": sum([r.weight for r in relations])
        }
        
        return structure
    
    def _calculate_structure_similarity(
        self, 
        struct1: Dict[str, Any], 
        struct2: Dict[str, Any]
    ) -> float:
        """计算两个结构的相似度（简化版）"""
        # 关系类型相似度（Jaccard）
        types1 = set(struct1['relation_types'])
        types2 = set(struct2['relation_types'])
        
        if len(types1) == 0 and len(types2) == 0:
            type_similarity = 1.0
        else:
            intersection = len(types1 & types2)
            union = len(types1 | types2)
            type_similarity = intersection / union if union > 0 else 0.0
        
        # 度数相似度
        out_diff = abs(struct1['outgoing_count'] - struct2['outgoing_count'])
        in_diff = abs(struct1['incoming_count'] - struct2['incoming_count'])
        max_degree = max(
            struct1['outgoing_count'] + struct1['incoming_count'],
            struct2['outgoing_count'] + struct2['incoming_count'],
            1
        )
        degree_similarity = 1.0 - (out_diff + in_diff) / max_degree
        
        # 综合相似度（加权平均）
        similarity = 0.6 * type_similarity + 0.4 * degree_similarity
        
        return similarity
