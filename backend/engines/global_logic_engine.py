"""
全局逻辑学习引擎
学习整本文件的全局结构、内容风格、一致性约束和评分权重
"""
from typing import Dict, List
from database import db
import json


class GlobalLogicEngine:
    """全局逻辑学习引擎"""
    
    def __init__(self):
        """初始化全局逻辑引擎"""
        self.db = db
    
    def learn_global(
        self,
        tender_doc: Dict,
        proposal_doc: Dict,
        chapter_packages: List[Dict]
    ) -> Dict:
        """
        学习全局逻辑
        
        Args:
            tender_doc: 招标文件 {id, filename, chapters, ...}
            proposal_doc: 投标文件 {id, filename, chapters, ...}
            chapter_packages: 章节逻辑包列表
            
        Returns:
            dict: 全局逻辑包
        """
        tender_id = tender_doc['id']
        
        # 1. 学习全局结构
        structure_rules = self._learn_global_structure(tender_doc, proposal_doc)
        self._save_global_structure_rules(tender_id, structure_rules)
        
        # 2. 学习内容风格
        content_rules = self._learn_global_content_style(tender_doc, proposal_doc)
        self._save_global_content_rules(tender_id, content_rules)
        
        # 3. 学习一致性约束
        consistency_rules = self._learn_consistency_constraints(
            tender_doc, proposal_doc, chapter_packages
        )
        self._save_global_consistency_rules(tender_id, consistency_rules)
        
        # 4. 学习评分引擎权重
        scoring_rules = self._learn_global_scoring(tender_doc, chapter_packages)
        self._save_global_scoring_rules(tender_id, scoring_rules)
        
        return {
            'tender_id': tender_id,
            'structure_rules': structure_rules,
            'content_rules': content_rules,
            'consistency_rules': consistency_rules,
            'scoring_rules': scoring_rules
        }
    
    def _learn_global_structure(self, tender: Dict, proposal: Dict) -> List[Dict]:
        """学习全局结构规则"""
        rules = []
        
        # 目录结构
        tender_chapters = tender.get('chapters', [])
        proposal_chapters = proposal.get('chapters', [])
        
        rules.append({
            'rule_type': 'toc_structure',
            'description': '目录结构要求',
            'required_chapters': [ch['chapter_title'] for ch in tender_chapters],
            'chapter_order': [ch['chapter_number'] for ch in tender_chapters],
            'total_chapters': len(tender_chapters)
        })
        
        # 章节层次
        max_level = max([ch.get('chapter_level', 1) for ch in tender_chapters], default=3)
        rules.append({
            'rule_type': 'chapter_hierarchy',
            'description': '章节层次深度',
            'max_depth': max_level,
            'recommended_depth': max_level
        })
        
        # 文档组织方式
        rules.append({
            'rule_type': 'document_organization',
            'description': '文档组织方式',
            'pattern': 'standard',  # standard/custom
            'has_appendix': len(tender_chapters) > 10,
            'has_summary': True
        })
        
        return rules
    
    def _learn_global_content_style(self, tender: Dict, proposal: Dict) -> List[Dict]:
        """学习全局内容风格"""
        rules = []
        
        # 语言风格
        rules.append({
            'rule_type': 'language_style',
            'description': '语言风格',
            'formality': 'formal',  # formal/semi-formal/informal
            'tone': 'professional',  # professional/technical/persuasive
            'person': 'third'  # first/third
        })
        
        # 术语一致性
        rules.append({
            'rule_type': 'terminology_consistency',
            'description': '术语一致性',
            'standard_terms': self._extract_standard_terms(tender),
            'avoid_terms': [],
            'preferred_expressions': {}
        })
        
        # 格式规范
        rules.append({
            'rule_type': 'formatting_standards',
            'description': '格式规范',
            'font_requirements': '宋体, 小四',
            'line_spacing': 1.5,
            'margin': '2.5cm',
            'page_numbering': True
        })
        
        return rules
    
    def _learn_consistency_constraints(
        self,
        tender: Dict,
        proposal: Dict,
        chapter_packages: List[Dict]
    ) -> List[Dict]:
        """学习一致性约束"""
        rules = []
        
        # 跨章节引用一致性
        rules.append({
            'rule_type': 'cross_reference_consistency',
            'description': '跨章节引用一致性',
            'enforce_numbering': True,
            'enforce_naming': True
        })
        
        # 数据一致性
        rules.append({
            'rule_type': 'data_consistency',
            'description': '数据一致性',
            'check_quantities': True,
            'check_dates': True,
            'check_names': True,
            'tolerance': 0.01
        })
        
        # 逻辑一致性
        rules.append({
            'rule_type': 'logic_consistency',
            'description': '逻辑一致性',
            'check_conflicts': True,
            'check_completeness': True
        })
        
        return rules
    
    def _learn_global_scoring(self, tender: Dict, chapter_packages: List[Dict]) -> List[Dict]:
        """学习全局评分权重"""
        rules = []
        
        # 提取所有章节的评分规则
        all_scoring_rules = []
        for pkg in chapter_packages:
            all_scoring_rules.extend(pkg.get('scoring_rules', []))
        
        # 计算总分和权重
        total_score = sum([rule.get('max_score', 0) for rule in all_scoring_rules])
        
        # 按类别分组
        categories = {}
        for rule in all_scoring_rules:
            category = rule.get('category', 'other')
            if category not in categories:
                categories[category] = {'count': 0, 'total_score': 0}
            categories[category]['count'] += 1
            categories[category]['total_score'] += rule.get('max_score', 0)
        
        # 生成权重规则
        for category, stats in categories.items():
            rules.append({
                'dimension': category,
                'weight': stats['total_score'] / total_score if total_score > 0 else 0,
                'max_score': stats['total_score'],
                'criterion_count': stats['count']
            })
        
        return rules
    
    def _extract_standard_terms(self, tender: Dict) -> List[str]:
        """提取标准术语"""
        # 简化实现
        return ['施工组织设计', '质量管理体系', '安全文明施工', '进度计划']
    
    # ========== 数据库保存方法 ==========
    
    def _save_global_structure_rules(self, tender_id: str, rules: List[Dict]):
        """保存全局结构规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO global_structure_rules (
                    tender_file_id, rule_type, rule_content, parameters, is_active
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                tender_id,
                rule['rule_type'],
                rule.get('description', ''),
                json.dumps(rule),
                True
            ))
    
    def _save_global_content_rules(self, tender_id: str, rules: List[Dict]):
        """保存全局内容规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO global_content_rules (
                    tender_file_id, rule_type, rule_content, style_guide, is_active
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                tender_id,
                rule['rule_type'],
                rule.get('description', ''),
                json.dumps(rule),
                True
            ))
    
    def _save_global_consistency_rules(self, tender_id: str, rules: List[Dict]):
        """保存全局一致性规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO global_consistency_rules (
                    tender_file_id, rule_type, rule_content, 
                    validation_logic, is_active
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                tender_id,
                rule['rule_type'],
                rule.get('description', ''),
                json.dumps(rule),
                True
            ))
    
    def _save_global_scoring_rules(self, tender_id: str, rules: List[Dict]):
        """保存全局评分规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO global_scoring_rules (
                    tender_file_id, dimension, weight, 
                    max_score, parameters, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                tender_id,
                rule['dimension'],
                rule.get('weight', 0),
                rule.get('max_score', 0),
                json.dumps(rule),
                True
            ))
