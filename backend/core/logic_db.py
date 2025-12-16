"""
统一规则数据库访问层 (DAL)
所有MCP都通过这个接口访问和管理逻辑规则
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sys
from pathlib import Path

# 添加 mcp-servers/shared 到路径
shared_path = str(Path(__file__).parent.parent.parent / 'mcp-servers' / 'shared')
sys.path.insert(0, shared_path)

from rule_schema import Rule, RuleType, RulePriority, RuleSource, RulePackage

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))

from database import db
from core.logger import logger


class LogicDatabaseDAL:
    """
    逻辑规则数据库访问层
    
    统一管理所有规则，三个MCP（学习、检查、生成）都通过这个接口交互
    """
    
    def __init__(self):
        self.db = db
    
    # ===================== 插入操作 =====================
    
    def add_rule(self, rule: Rule) -> str:
        """
        添加单条规则
        
        Args:
            rule: Rule 对象
            
        Returns:
            规则ID
        """
        try:
            result = self.db.query_one(
                """
                INSERT INTO logic_database (
                    rule_type, priority, source,
                    condition, condition_description,
                    description, pattern,
                    action, action_description,
                    constraints, scope,
                    confidence, version, tags,
                    reference, fix_suggestion,
                    examples, counter_examples,
                    is_active
                ) VALUES (
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s
                ) RETURNING id
                """,
                (
                    rule.type.value, rule.priority.value, rule.source.value,
                    json.dumps(rule.condition) if rule.condition else None,
                    rule.condition_description,
                    rule.description, rule.pattern,
                    json.dumps(rule.action) if rule.action else None,
                    rule.action_description,
                    json.dumps(rule.constraints) if rule.constraints else None,
                    json.dumps(rule.scope) if rule.scope else None,
                    float(rule.confidence), rule.version, rule.tags,
                    json.dumps(rule.reference) if rule.reference else None,
                    rule.fix_suggestion,
                    rule.examples or [],
                    rule.counter_examples or [],
                    True
                )
            )
            rule_id = result['id']
            logger.info(f"Rule added: {rule_id} (type={rule.type}, source={rule.source})")
            return str(rule_id)
        
        except Exception as e:
            logger.error(f"Failed to add rule: {e}", exc_info=True)
            raise
    
    def add_rules_batch(self, rules: List[Rule]) -> List[str]:
        """
        批量添加规则
        
        Args:
            rules: Rule 列表
            
        Returns:
            规则ID列表
        """
        rule_ids = []
        for rule in rules:
            rule_id = self.add_rule(rule)
            rule_ids.append(rule_id)
        
        logger.info(f"Batch added {len(rule_ids)} rules")
        return rule_ids
    
    # ===================== 查询操作 =====================
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        获取单条规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Rule 对象或 None
        """
        try:
            result = self.db.query_one(
                "SELECT * FROM logic_database WHERE id = %s",
                (rule_id,)
            )
            
            if not result:
                return None
            
            return self._row_to_rule(result)
        
        except Exception as e:
            logger.error(f"Failed to get rule {rule_id}: {e}", exc_info=True)
            return None
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """
        按类型获取规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            Rule 列表
        """
        try:
            results = self.db.query(
                "SELECT * FROM logic_database WHERE rule_type = %s AND is_active = TRUE ORDER BY priority DESC, created_at DESC",
                (rule_type.value,)
            )
            
            return [self._row_to_rule(row) for row in results]
        
        except Exception as e:
            logger.error(f"Failed to get rules by type {rule_type}: {e}", exc_info=True)
            return []
    
    def get_rules_by_priority(self, priority: RulePriority) -> List[Rule]:
        """
        按优先级获取规则
        
        Args:
            priority: 优先级
            
        Returns:
            Rule 列表
        """
        try:
            results = self.db.query(
                "SELECT * FROM logic_database WHERE priority = %s AND is_active = TRUE ORDER BY created_at DESC",
                (priority.value,)
            )
            
            return [self._row_to_rule(row) for row in results]
        
        except Exception as e:
            logger.error(f"Failed to get rules by priority {priority}: {e}", exc_info=True)
            return []
    
    def get_rules_by_source(self, source: RuleSource) -> List[Rule]:
        """
        按来源获取规则
        
        Args:
            source: 规则来源
            
        Returns:
            Rule 列表
        """
        try:
            results = self.db.query(
                "SELECT * FROM logic_database WHERE source = %s AND is_active = TRUE ORDER BY created_at DESC",
                (source.value,)
            )
            
            return [self._row_to_rule(row) for row in results]
        
        except Exception as e:
            logger.error(f"Failed to get rules by source {source}: {e}", exc_info=True)
            return []
    
    def get_all_rules(self, active_only: bool = True) -> List[Rule]:
        """
        获取所有规则
        
        Args:
            active_only: 仅返回启用的规则
            
        Returns:
            Rule 列表
        """
        try:
            if active_only:
                results = self.db.query(
                    "SELECT * FROM logic_database WHERE is_active = TRUE ORDER BY priority DESC, created_at DESC"
                )
            else:
                results = self.db.query(
                    "SELECT * FROM logic_database ORDER BY created_at DESC"
                )
            
            return [self._row_to_rule(row) for row in results]
        
        except Exception as e:
            logger.error(f"Failed to get all rules: {e}", exc_info=True)
            return []
    
    def search_rules(self, keyword: str, rule_type: Optional[RuleType] = None) -> List[Rule]:
        """
        搜索规则（按描述或条件关键词）
        
        Args:
            keyword: 搜索关键词
            rule_type: 可选的规则类型过滤
            
        Returns:
            Rule 列表
        """
        try:
            if rule_type:
                results = self.db.query(
                    """
                    SELECT * FROM logic_database 
                    WHERE rule_type = %s AND is_active = TRUE
                    AND (description ILIKE %s OR pattern ILIKE %s)
                    ORDER BY created_at DESC
                    """,
                    (rule_type.value, f"%{keyword}%", f"%{keyword}%")
                )
            else:
                results = self.db.query(
                    """
                    SELECT * FROM logic_database 
                    WHERE is_active = TRUE
                    AND (description ILIKE %s OR pattern ILIKE %s)
                    ORDER BY created_at DESC
                    """,
                    (f"%{keyword}%", f"%{keyword}%")
                )
            
            return [self._row_to_rule(row) for row in results]
        
        except Exception as e:
            logger.error(f"Failed to search rules: {e}", exc_info=True)
            return []
    
    # ===================== 更新操作 =====================
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新规则
        
        Args:
            rule_id: 规则ID
            updates: 更新字段字典
            
        Returns:
            是否更新成功
        """
        try:
            # 仅允许更新特定字段
            allowed_fields = {
                'priority', 'description', 'pattern', 'action', 
                'action_description', 'constraints', 'fix_suggestion',
                'examples', 'counter_examples', 'confidence'
            }
            
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not filtered_updates:
                logger.warning(f"No valid fields to update for rule {rule_id}")
                return False
            
            # 构建更新语句
            set_clause = ", ".join([f"{k} = %s" for k in filtered_updates.keys()])
            values = list(filtered_updates.values()) + [rule_id]
            
            query = f"""
                UPDATE logic_database 
                SET {set_clause}, updated_at = now()
                WHERE id = %s
            """
            
            self.db.execute(query, values)
            logger.info(f"Rule {rule_id} updated: {filtered_updates}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update rule {rule_id}: {e}", exc_info=True)
            return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        return self.update_rule(rule_id, {'is_active': False})
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        return self.update_rule(rule_id, {'is_active': True})
    
    # ===================== 删除操作 =====================
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        删除规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否删除成功
        """
        try:
            self.db.execute(
                "DELETE FROM logic_database WHERE id = %s",
                (rule_id,)
            )
            logger.info(f"Rule {rule_id} deleted")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete rule {rule_id}: {e}", exc_info=True)
            return False
    
    # ===================== 统计操作 =====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取规则库统计"""
        try:
            # 按类型统计
            type_stats = self.db.query(
                "SELECT rule_type, COUNT(*) as count FROM logic_database WHERE is_active = TRUE GROUP BY rule_type"
            )
            
            # 按优先级统计
            priority_stats = self.db.query(
                "SELECT priority, COUNT(*) as count FROM logic_database WHERE is_active = TRUE GROUP BY priority"
            )
            
            # 总数
            total = self.db.query_one(
                "SELECT COUNT(*) as count FROM logic_database WHERE is_active = TRUE"
            )['count']
            
            return {
                'total_rules': total,
                'by_type': {row['rule_type']: row['count'] for row in type_stats},
                'by_priority': {row['priority']: row['count'] for row in priority_stats},
            }
        
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {}
    
    # ===================== 规则包操作 =====================
    
    def create_rule_package(self, name: str, rule_ids: List[str]) -> RulePackage:
        """
        创建规则包
        
        Args:
            name: 规则包名称
            rule_ids: 规则ID列表
            
        Returns:
            RulePackage 对象
        """
        package = RulePackage(name=name)
        
        for rule_id in rule_ids:
            rule = self.get_rule(rule_id)
            if rule:
                package.add_rule(rule)
        
        logger.info(f"Rule package created: {name} with {len(rule_ids)} rules")
        return package
    
    # ===================== 辅助方法 =====================
    
    def _row_to_rule(self, row: Dict[str, Any]) -> Rule:
        """将数据库行转换为 Rule 对象"""
        # JSONB字段在psycopg2中已经被解析为dict，不需要json.loads
        # 但如果是字符串则需要解析
        def parse_json_field(field_value):
            if field_value is None:
                return None
            if isinstance(field_value, dict):
                return field_value
            if isinstance(field_value, str):
                return json.loads(field_value)
            return field_value
        
        return Rule(
            id=str(row['id']),
            type=RuleType(row['rule_type']),
            priority=RulePriority(row['priority']),
            source=RuleSource(row['source']),
            condition=parse_json_field(row['condition']),
            condition_description=row['condition_description'],
            description=row['description'],
            pattern=row['pattern'],
            action=parse_json_field(row['action']),
            action_description=row['action_description'],
            constraints=parse_json_field(row['constraints']),
            scope=parse_json_field(row['scope']),
            confidence=float(row['confidence']),
            version=row['version'],
            tags=row['tags'] or [],
            reference=parse_json_field(row['reference']),
            fix_suggestion=row['fix_suggestion'],
            examples=row['examples'] or [],
            counter_examples=row['counter_examples'] or [],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )


# 全局实例
logic_db = LogicDatabaseDAL()
