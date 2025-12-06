"""
深度逻辑学习引擎 - 学习招标-投标的对应逻辑

功能：
1. 分析招标需求 -> 投标响应的对应关系
2. 生成"标书生成逻辑库"（如何根据招标要求生成投标内容）
3. 生成"标书检查逻辑库"（如何验证投标文件的合规性和质量）
4. 支持持续学习和逻辑优化
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from core.logger import logger
from core.llm_router import get_llm_router, TaskType
from engines.document_parser import ParsedDocument, KnowledgeBase, KnowledgeEntry


@dataclass
class GenerationRule:
    """生成规则 - 描述如何根据招标要求生成投标内容"""
    rule_id: str
    
    # 触发条件
    trigger_type: str  # "requirement", "technical", "evaluation"
    trigger_pattern: str  # 触发模式（如"性能要求: CPU >= 8核"）
    
    # 生成策略
    generation_strategy: str  # "direct_match", "enhanced_response", "creative"
    response_template: str  # 响应模板
    
    # 示例
    examples: List[Dict[str, str]]  # [{"input": "招标要求", "output": "投标响应"}]
    
    # 约束条件
    constraints: List[str]  # 必须满足的约束
    
    # 质量指标
    success_rate: float  # 历史成功率 0-100
    confidence: float  # 规则置信度 0-100
    
    # 元数据
    learned_from: List[str]  # 学习来源（pair_id列表）
    created_time: str
    last_updated: str
    usage_count: int  # 使用次数
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class ValidationRule:
    """验证规则 - 描述如何检查投标文件"""
    rule_id: str
    
    # 检查类型
    check_type: str  # "compliance", "completeness", "quality", "consistency"
    check_target: str  # 检查对象（章节、字段等）
    
    # 检查逻辑
    validation_logic: str  # 验证逻辑描述
    check_method: str  # "rule_based", "llm_based", "hybrid"
    
    # 判断标准
    pass_criteria: str  # 通过标准
    fail_examples: List[str]  # 失败案例
    
    # 严重程度
    severity: str  # "critical", "major", "minor"
    
    # 修复建议
    fix_suggestions: List[str]  # 修复建议
    
    # 质量指标
    precision: float  # 精确率 0-100
    recall: float  # 召回率 0-100
    
    # 元数据
    learned_from: List[str]
    created_time: str
    last_updated: str
    usage_count: int
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class GenerationLogicDB:
    """标书生成逻辑库"""
    db_id: str
    rules: List[GenerationRule]
    
    # 统计信息
    total_rules: int
    rule_types: Dict[str, int]
    avg_success_rate: float
    
    # 存储路径
    storage_path: str
    created_time: str
    last_updated: str
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        if not self.total_rules:
            self.total_rules = len(self.rules)


@dataclass
class ValidationLogicDB:
    """标书检查逻辑库"""
    db_id: str
    rules: List[ValidationRule]
    
    # 统计信息
    total_rules: int
    rule_types: Dict[str, int]
    avg_precision: float
    avg_recall: float
    
    # 存储路径
    storage_path: str
    created_time: str
    last_updated: str
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        if not self.total_rules:
            self.total_rules = len(self.rules)


class LogicLearningEngine:
    """深度逻辑学习引擎"""
    
    def __init__(self):
        """初始化逻辑学习引擎"""
        self.llm_router = get_llm_router()
        logger.info("LogicLearningEngine initialized")
    
    async def learn_generation_logic(
        self,
        tender_doc: ParsedDocument,
        proposal_doc: ParsedDocument,
        pair_id: str
    ) -> List[GenerationRule]:
        """
        从招标-投标配对中学习生成逻辑
        
        Args:
            tender_doc: 招标文档
            proposal_doc: 投标文档
            pair_id: 配对ID
            
        Returns:
            生成规则列表
        """
        logger.info(f"Learning generation logic from pair: {pair_id}")
        
        rules = []
        rule_counter = 1
        
        # 遍历配对的章节，学习对应关系
        for tender_ch in tender_doc.chapters:
            # 找到对应的投标章节
            proposal_ch = self._find_matching_chapter(
                tender_ch.chapter_id,
                proposal_doc.chapters
            )
            
            if not proposal_ch:
                continue
            
            # 学习需求响应规则
            for req in tender_ch.requirements:
                rule = await self._learn_requirement_response(
                    requirement=req,
                    tender_chapter=tender_ch,
                    proposal_chapter=proposal_ch,
                    rule_id=f"gen_{pair_id}_{rule_counter:04d}",
                    pair_id=pair_id
                )
                
                if rule:
                    rules.append(rule)
                    rule_counter += 1
            
            # 学习技术规格响应规则
            for tech_spec in tender_ch.technical_specs:
                rule = await self._learn_technical_response(
                    tech_spec=tech_spec,
                    tender_chapter=tender_ch,
                    proposal_chapter=proposal_ch,
                    rule_id=f"gen_{pair_id}_{rule_counter:04d}",
                    pair_id=pair_id
                )
                
                if rule:
                    rules.append(rule)
                    rule_counter += 1
        
        logger.info(f"Learned {len(rules)} generation rules")
        
        return rules
    
    async def _learn_requirement_response(
        self,
        requirement: str,
        tender_chapter,
        proposal_chapter,
        rule_id: str,
        pair_id: str
    ) -> Optional[GenerationRule]:
        """
        使用LLM学习需求响应规则
        
        Args:
            requirement: 招标需求
            tender_chapter: 招标章节
            proposal_chapter: 投标章节
            rule_id: 规则ID
            pair_id: 配对ID
            
        Returns:
            生成规则
        """
        prompt = f"""
分析以下招标需求和对应的投标响应，提取生成规则：

招标需求：
{requirement}

招标章节关键点：
{', '.join(tender_chapter.key_points[:5])}

投标响应（章节 {proposal_chapter.chapter_id}）：
{proposal_chapter.summary}

投标关键点：
{', '.join(proposal_chapter.key_points[:5])}

请以JSON格式返回生成规则：
{{
  "trigger_pattern": "需求的特征模式（如：性能要求，CPU相关）",
  "generation_strategy": "direct_match / enhanced_response / creative",
  "response_template": "响应模板，用{{placeholder}}标记可替换部分",
  "constraints": ["约束1", "约束2"],
  "confidence": 置信度(0-100)
}}

注意：
1. 提取可复用的模式，不要过度具体化
2. 响应模板要足够灵活
3. 返回纯JSON
"""
        
        try:
            result = await self.llm_router.generate_text(
                prompt=prompt,
                system_prompt="你是招投标逻辑学习专家，擅长提取可复用的生成规则。",
                task_type=TaskType.ANALYSIS,
                max_tokens=1000
            )
            
            # 解析JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            
            data = json.loads(result)
            
            rule = GenerationRule(
                rule_id=rule_id,
                trigger_type="requirement",
                trigger_pattern=data.get("trigger_pattern", requirement),
                generation_strategy=data.get("generation_strategy", "direct_match"),
                response_template=data.get("response_template", ""),
                examples=[{
                    "input": requirement,
                    "output": proposal_chapter.summary
                }],
                constraints=data.get("constraints", []),
                success_rate=100,  # 初始假设100%
                confidence=data.get("confidence", 80),
                learned_from=[pair_id],
                created_time=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                usage_count=0
            )
            
            return rule
            
        except Exception as e:
            logger.warning(f"Failed to learn requirement response: {e}")
            return None
    
    async def _learn_technical_response(
        self,
        tech_spec: Dict[str, Any],
        tender_chapter,
        proposal_chapter,
        rule_id: str,
        pair_id: str
    ) -> Optional[GenerationRule]:
        """学习技术规格响应规则"""
        # 找到投标文档中对应的技术规格
        matching_spec = None
        for p_spec in proposal_chapter.technical_specs:
            if p_spec.get('item') == tech_spec.get('item'):
                matching_spec = p_spec
                break
        
        if not matching_spec:
            return None
        
        # 简化版：直接创建规则
        rule = GenerationRule(
            rule_id=rule_id,
            trigger_type="technical",
            trigger_pattern=f"{tech_spec.get('item', '')}: {tech_spec.get('spec', '')}",
            generation_strategy="enhanced_response",
            response_template=f"{{item}}: {{spec}} (满足并超出要求)",
            examples=[{
                "input": str(tech_spec),
                "output": str(matching_spec)
            }],
            constraints=["mandatory" if tech_spec.get('mandatory') else "optional"],
            success_rate=100,
            confidence=90,
            learned_from=[pair_id],
            created_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            usage_count=0
        )
        
        return rule
    
    async def learn_validation_logic(
        self,
        tender_doc: ParsedDocument,
        proposal_doc: ParsedDocument,
        pair_id: str
    ) -> List[ValidationRule]:
        """
        从招标-投标配对中学习验证逻辑
        
        Args:
            tender_doc: 招标文档
            proposal_doc: 投标文档
            pair_id: 配对ID
            
        Returns:
            验证规则列表
        """
        logger.info(f"Learning validation logic from pair: {pair_id}")
        
        rules = []
        rule_counter = 1
        
        # 学习合规性检查规则
        for tender_ch in tender_doc.chapters:
            # 检查必须项
            for req in tender_ch.requirements:
                rule = await self._learn_compliance_check(
                    requirement=req,
                    tender_chapter=tender_ch,
                    rule_id=f"val_{pair_id}_{rule_counter:04d}",
                    pair_id=pair_id
                )
                
                if rule:
                    rules.append(rule)
                    rule_counter += 1
            
            # 检查技术规格
            for spec in tender_ch.technical_specs:
                if spec.get('mandatory'):
                    rule = ValidationRule(
                        rule_id=f"val_{pair_id}_{rule_counter:04d}",
                        check_type="compliance",
                        check_target=spec.get('item', ''),
                        validation_logic=f"检查是否满足: {spec.get('spec', '')}",
                        check_method="rule_based",
                        pass_criteria=f"规格 >= {spec.get('spec', '')}",
                        fail_examples=[],
                        severity="critical",
                        fix_suggestions=[f"确保{spec.get('item', '')}满足{spec.get('spec', '')}"],
                        precision=100,
                        recall=100,
                        learned_from=[pair_id],
                        created_time=datetime.now().isoformat(),
                        last_updated=datetime.now().isoformat(),
                        usage_count=0
                    )
                    rules.append(rule)
                    rule_counter += 1
        
        # 学习完整性检查规则
        completeness_rule = ValidationRule(
            rule_id=f"val_{pair_id}_{rule_counter:04d}",
            check_type="completeness",
            check_target="all_chapters",
            validation_logic="检查是否所有招标要求的章节都有对应响应",
            check_method="hybrid",
            pass_criteria="所有必需章节都存在且非空",
            fail_examples=["缺少技术方案章节", "商务条款章节为空"],
            severity="critical",
            fix_suggestions=["补充缺失章节", "完善空白章节内容"],
            precision=100,
            recall=100,
            learned_from=[pair_id],
            created_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            usage_count=0
        )
        rules.append(completeness_rule)
        
        logger.info(f"Learned {len(rules)} validation rules")
        
        return rules
    
    async def _learn_compliance_check(
        self,
        requirement: str,
        tender_chapter,
        rule_id: str,
        pair_id: str
    ) -> Optional[ValidationRule]:
        """学习合规性检查规则"""
        rule = ValidationRule(
            rule_id=rule_id,
            check_type="compliance",
            check_target=requirement,
            validation_logic=f"检查投标文件是否响应了需求: {requirement}",
            check_method="llm_based",
            pass_criteria="明确响应了需求，提供了具体方案",
            fail_examples=["未提及该需求", "响应过于简单", "不符合要求"],
            severity="major",
            fix_suggestions=[f"补充对'{requirement}'的详细响应"],
            precision=90,
            recall=90,
            learned_from=[pair_id],
            created_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            usage_count=0
        )
        
        return rule
    
    def _find_matching_chapter(self, chapter_id: str, chapters: List) -> Optional[Any]:
        """查找匹配的章节"""
        for ch in chapters:
            if ch.chapter_id == chapter_id:
                return ch
        return None
    
    async def build_generation_logic_db(
        self,
        all_rules: List[GenerationRule],
        storage_path: str
    ) -> GenerationLogicDB:
        """
        构建生成逻辑库
        
        Args:
            all_rules: 所有生成规则
            storage_path: 存储路径
            
        Returns:
            生成逻辑库
        """
        # 去重和合并相似规则
        unique_rules = self._merge_similar_rules(all_rules)
        
        # 统计
        rule_types = {}
        total_success_rate = 0
        for rule in unique_rules:
            rule_types[rule.trigger_type] = rule_types.get(rule.trigger_type, 0) + 1
            total_success_rate += rule.success_rate
        
        avg_success_rate = total_success_rate / len(unique_rules) if unique_rules else 0
        
        db = GenerationLogicDB(
            db_id=f"gen_logic_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            rules=unique_rules,
            total_rules=len(unique_rules),
            rule_types=rule_types,
            avg_success_rate=avg_success_rate,
            storage_path=storage_path,
            created_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
        
        # 保存
        await self._save_generation_logic_db(db, storage_path)
        
        logger.info(f"Built generation logic DB with {len(unique_rules)} rules")
        
        return db
    
    async def build_validation_logic_db(
        self,
        all_rules: List[ValidationRule],
        storage_path: str
    ) -> ValidationLogicDB:
        """构建验证逻辑库"""
        unique_rules = all_rules  # 简化版：不做合并
        
        # 统计
        rule_types = {}
        total_precision = 0
        total_recall = 0
        for rule in unique_rules:
            rule_types[rule.check_type] = rule_types.get(rule.check_type, 0) + 1
            total_precision += rule.precision
            total_recall += rule.recall
        
        avg_precision = total_precision / len(unique_rules) if unique_rules else 0
        avg_recall = total_recall / len(unique_rules) if unique_rules else 0
        
        db = ValidationLogicDB(
            db_id=f"val_logic_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            rules=unique_rules,
            total_rules=len(unique_rules),
            rule_types=rule_types,
            avg_precision=avg_precision,
            avg_recall=avg_recall,
            storage_path=storage_path,
            created_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
        
        # 保存
        await self._save_validation_logic_db(db, storage_path)
        
        logger.info(f"Built validation logic DB with {len(unique_rules)} rules")
        
        return db
    
    def _merge_similar_rules(self, rules: List[GenerationRule]) -> List[GenerationRule]:
        """合并相似规则（简化版）"""
        # TODO: 实现更智能的规则合并
        return rules
    
    async def _save_generation_logic_db(self, db: GenerationLogicDB, storage_path: str):
        """保存生成逻辑库"""
        logic_dir = Path(storage_path) / "logic_db"
        logic_dir.mkdir(parents=True, exist_ok=True)
        
        db_file = logic_dir / f"{db.db_id}.json"
        
        db_data = {
            "db_id": db.db_id,
            "total_rules": db.total_rules,
            "rule_types": db.rule_types,
            "avg_success_rate": db.avg_success_rate,
            "created_time": db.created_time,
            "last_updated": db.last_updated,
            "rules": [asdict(rule) for rule in db.rules]
        }
        
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved generation logic DB: {db_file}")
    
    async def _save_validation_logic_db(self, db: ValidationLogicDB, storage_path: str):
        """保存验证逻辑库"""
        logic_dir = Path(storage_path) / "logic_db"
        logic_dir.mkdir(parents=True, exist_ok=True)
        
        db_file = logic_dir / f"{db.db_id}.json"
        
        db_data = {
            "db_id": db.db_id,
            "total_rules": db.total_rules,
            "rule_types": db.rule_types,
            "avg_precision": db.avg_precision,
            "avg_recall": db.avg_recall,
            "created_time": db.created_time,
            "last_updated": db.last_updated,
            "rules": [asdict(rule) for rule in db.rules]
        }
        
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved validation logic DB: {db_file}")
