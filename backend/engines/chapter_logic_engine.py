"""
章节级逻辑学习引擎
学习章节的结构、内容、工程量清单、强制要求和评分规则
"""
from typing import Dict, List, Optional
from database import db
import json
import uuid


class ChapterLogicEngine:
    """章节级逻辑学习引擎"""
    
    def __init__(self):
        """初始化章节逻辑引擎"""
        self.db = db
    
    def learn_chapter(
        self, 
        tender_chapter: Dict, 
        proposal_chapter: Dict, 
        boq: Optional[Dict] = None,
        custom_rules: Optional[List[Dict]] = None
    ) -> Dict:
        """
        学习章节对,生成章节逻辑包
        
        Args:
            tender_chapter: 招标章节 {id, chapter_title, content, ...}
            proposal_chapter: 投标章节 {id, chapter_title, content, ...}
            boq: 工程量清单 {items: [...]}
            custom_rules: 自定义规则列表
            
        Returns:
            dict: 章节逻辑包 {
                structure_rules, content_rules, boq_rules,
                mandatory_rules, scoring_rules, custom_rules
            }
        """
        chapter_id = tender_chapter['id']
        
        # 1. 学习结构规则
        structure_rules = self._learn_structure(tender_chapter, proposal_chapter)
        self._save_structure_rules(chapter_id, structure_rules)
        
        # 2. 学习内容规则
        content_rules = self._learn_content(tender_chapter, proposal_chapter)
        self._save_content_rules(chapter_id, content_rules)
        
        # 3. 学习工程量清单规则(如果有)
        boq_rules = []
        if boq:
            boq_rules = self._learn_boq(chapter_id, boq)
            self._save_boq_rules(chapter_id, boq_rules)
        
        # 4. 提取强制要求
        mandatory_rules = self._extract_mandatory_requirements(tender_chapter)
        self._save_mandatory_rules(chapter_id, mandatory_rules)
        
        # 5. 学习评分规则
        scoring_rules = self._learn_scoring_rules(tender_chapter, proposal_chapter)
        self._save_scoring_rules(chapter_id, scoring_rules)
        
        # 6. 保存自定义规则
        if custom_rules:
            self._save_custom_rules(chapter_id, custom_rules)
        
        return {
            'chapter_id': chapter_id,
            'structure_rules': structure_rules,
            'content_rules': content_rules,
            'boq_rules': boq_rules,
            'mandatory_rules': mandatory_rules,
            'scoring_rules': scoring_rules,
            'custom_rules': custom_rules or []
        }
    
    def _learn_structure(self, tender: Dict, proposal: Dict) -> List[Dict]:
        """
        学习结构规则
        
        分析招标和投标章节的结构差异,提取结构模式
        """
        rules = []
        
        # 分析小节数量
        tender_sections = self._extract_sections(tender['content'])
        proposal_sections = self._extract_sections(proposal['content'])
        
        rules.append({
            'rule_type': 'section_count',
            'description': '小节数量要求',
            'tender_value': len(tender_sections),
            'proposal_value': len(proposal_sections),
            'min_sections': len(tender_sections),
            'recommended_sections': len(proposal_sections)
        })
        
        # 分析标题层级
        rules.append({
            'rule_type': 'title_hierarchy',
            'description': '标题层级结构',
            'required_levels': ['h1', 'h2', 'h3'],
            'pattern': 'numeric'  # 或 'chinese'
        })
        
        # 分析内容组织
        rules.append({
            'rule_type': 'content_organization',
            'description': '内容组织方式',
            'pattern': 'sequential',  # sequential/parallel/nested
            'required_components': ['description', 'method', 'plan']
        })
        
        return rules
    
    def _learn_content(self, tender: Dict, proposal: Dict) -> List[Dict]:
        """
        学习内容规则
        
        分析内容的写作风格、关键词、句式等
        """
        rules = []
        
        # 关键词分析
        tender_keywords = self._extract_keywords(tender['content'])
        proposal_keywords = self._extract_keywords(proposal['content'])
        
        rules.append({
            'rule_type': 'required_keywords',
            'description': '必须包含的关键词',
            'keywords': tender_keywords[:20],  # 前20个高频词
            'source': 'tender'
        })
        
        # 响应关键词(投标特有)
        response_keywords = [k for k in proposal_keywords if k not in tender_keywords]
        rules.append({
            'rule_type': 'response_keywords',
            'description': '响应性关键词',
            'keywords': response_keywords[:10],
            'source': 'proposal'
        })
        
        # 内容长度要求
        rules.append({
            'rule_type': 'content_length',
            'description': '内容长度要求',
            'min_length': len(tender['content']) * 0.8,
            'max_length': len(tender['content']) * 1.5,
            'recommended_length': len(proposal['content'])
        })
        
        # 段落密度
        tender_paragraphs = tender['content'].count('\n\n') + 1
        proposal_paragraphs = proposal['content'].count('\n\n') + 1
        
        rules.append({
            'rule_type': 'paragraph_density',
            'description': '段落密度',
            'tender_paragraphs': tender_paragraphs,
            'proposal_paragraphs': proposal_paragraphs,
            'recommended_density': proposal_paragraphs / len(proposal['content']) * 1000
        })
        
        return rules
    
    def _learn_boq(self, chapter_id: str, boq: Dict) -> List[Dict]:
        """
        学习工程量清单规则
        
        Args:
            chapter_id: 章节ID
            boq: 工程量清单数据
        """
        rules = []
        
        if 'items' in boq:
            for item in boq['items']:
                rules.append({
                    'rule_type': 'boq_item',
                    'item_code': item.get('code', ''),
                    'item_name': item.get('name', ''),
                    'unit': item.get('unit', ''),
                    'quantity': item.get('quantity', 0),
                    'unit_price': item.get('unit_price', 0),
                    'total_price': item.get('total_price', 0),
                    'description': item.get('description', '')
                })
        
        return rules
    
    def _extract_mandatory_requirements(self, tender: Dict) -> List[Dict]:
        """
        提取强制要求
        
        识别标书中的"必须"、"不得"、"应当"等强制性语句
        """
        mandatory_rules = []
        content = tender['content']
        
        # 强制性关键词
        mandatory_keywords = ['必须', '不得', '不能', '禁止', '严禁', '应当', '应', '需要']
        
        lines = content.split('\n')
        for line in lines:
            for keyword in mandatory_keywords:
                if keyword in line:
                    mandatory_rules.append({
                        'requirement_type': self._classify_requirement(keyword),
                        'keyword': keyword,
                        'description': line.strip(),
                        'is_negative': keyword in ['不得', '不能', '禁止', '严禁'],
                        'priority': 'high'
                    })
                    break
        
        return mandatory_rules
    
    def _learn_scoring_rules(self, tender: Dict, proposal: Dict) -> List[Dict]:
        """
        学习评分规则
        
        从标书中提取评分标准
        """
        scoring_rules = []
        content = tender['content']
        
        # 查找评分关键词
        scoring_keywords = ['分', '得分', '评分', '分值', '满分']
        
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line for keyword in scoring_keywords):
                # 尝试提取分数
                import re
                score_match = re.search(r'(\d+)分', line)
                if score_match:
                    score_value = int(score_match.group(1))
                    scoring_rules.append({
                        'criterion': line.strip(),
                        'max_score': score_value,
                        'description': line.strip(),
                        'category': self._classify_scoring_criterion(line)
                    })
        
        return scoring_rules
    
    # ========== 辅助方法 ==========
    
    def _extract_sections(self, content: str) -> List[str]:
        """提取小节"""
        import re
        sections = re.findall(r'^(\d+\.\d+)\s+(.+)$', content, re.MULTILINE)
        return sections
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词(简化版,实际应使用NLP)"""
        # 简化实现:分词 + 去停用词 + 统计频率
        import re
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', content)  # 提取中文词
        from collections import Counter
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(50)]
    
    def _classify_requirement(self, keyword: str) -> str:
        """分类强制要求"""
        if keyword in ['必须', '应当', '应', '需要']:
            return 'positive'
        elif keyword in ['不得', '不能', '禁止', '严禁']:
            return 'negative'
        return 'neutral'
    
    def _classify_scoring_criterion(self, text: str) -> str:
        """分类评分标准"""
        if '技术' in text or '方案' in text:
            return 'technical'
        elif '商务' in text or '价格' in text:
            return 'commercial'
        elif '资质' in text or '业绩' in text:
            return 'qualification'
        return 'other'
    
    # ========== 数据库保存方法 ==========
    
    def _save_structure_rules(self, chapter_id: str, rules: List[Dict]):
        """保存结构规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO chapter_structure_rules (
                    chapter_id, rule_type, rule_content, parameters, priority, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                chapter_id,
                rule['rule_type'],
                rule.get('description', ''),
                json.dumps(rule),
                1.0,
                True
            ))
    
    def _save_content_rules(self, chapter_id: str, rules: List[Dict]):
        """保存内容规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO chapter_content_rules (
                    chapter_id, rule_type, rule_content, keywords, 
                    constraints, priority, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                chapter_id,
                rule['rule_type'],
                rule.get('description', ''),
                json.dumps(rule.get('keywords', [])),
                json.dumps(rule),
                1.0,
                True
            ))
    
    def _save_boq_rules(self, chapter_id: str, rules: List[Dict]):
        """保存工程量清单规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO chapter_boq_rules (
                    chapter_id, item_code, item_name, unit, 
                    quantity, unit_price, total_price, description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                chapter_id,
                rule.get('item_code', ''),
                rule.get('item_name', ''),
                rule.get('unit', ''),
                rule.get('quantity', 0),
                rule.get('unit_price', 0),
                rule.get('total_price', 0),
                rule.get('description', '')
            ))
    
    def _save_mandatory_rules(self, chapter_id: str, rules: List[Dict]):
        """保存强制要求"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO chapter_mandatory_rules (
                    chapter_id, requirement_type, keyword, 
                    description, is_negative, priority, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                chapter_id,
                rule['requirement_type'],
                rule['keyword'],
                rule['description'],
                rule['is_negative'],
                rule.get('priority', 'medium'),
                True
            ))
    
    def _save_scoring_rules(self, chapter_id: str, rules: List[Dict]):
        """保存评分规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO chapter_scoring_rules (
                    chapter_id, criterion, max_score, 
                    description, category, weight, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                chapter_id,
                rule['criterion'],
                rule.get('max_score', 0),
                rule.get('description', ''),
                rule.get('category', 'other'),
                1.0,
                True
            ))
    
    def _save_custom_rules(self, chapter_id: str, rules: List[Dict]):
        """保存自定义规则"""
        for rule in rules:
            self.db.execute("""
                INSERT INTO chapter_custom_rules (
                    chapter_id, rule_name, rule_type, 
                    rule_content, parameters, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                chapter_id,
                rule.get('rule_name', ''),
                rule.get('rule_type', 'custom'),
                rule.get('rule_content', ''),
                json.dumps(rule.get('parameters', {})),
                True
            ))
