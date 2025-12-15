"""
统一的规则表达框架
所有 MCP 服务（学习、检查、生成）共享的规则定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import uuid


class RuleType(str, Enum):
    """规则类型枚举"""
    STRUCTURE = "structure"              # 结构规则
    CONTENT = "content"                  # 内容规则
    MANDATORY = "mandatory"              # 强制要求
    SCORING = "scoring"                  # 评分规则
    CONSISTENCY = "consistency"          # 一致性约束
    FORMATTING = "formatting"            # 格式规范
    TERMINOLOGY = "terminology"          # 术语定义


class RulePriority(str, Enum):
    """规则优先级"""
    CRITICAL = "critical"                # 致命（必须满足）
    HIGH = "high"                        # 高（强烈建议）
    MEDIUM = "medium"                    # 中（建议）
    LOW = "low"                          # 低（参考）


class RuleSource(str, Enum):
    """规则来源"""
    CHAPTER_LEARNING = "chapter_learning"        # 章节级学习
    GLOBAL_LEARNING = "global_learning"          # 全局级学习
    MANUAL = "manual"                            # 手动输入
    REPORT_ANALYSIS = "report_analysis"          # 检查报告分析


class Rule(BaseModel):
    """
    统一的规则表达
    
    每条规则都能被三个 MCP 理解：
    - 学习 MCP：生成这样的规则
    - 检查 MCP：使用规则来验证标书
    - 生成 MCP：根据规则生成标书内容
    """
    
    # 基本属性
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="规则唯一ID")
    type: RuleType = Field(description="规则类型")
    priority: RulePriority = Field(description="优先级")
    source: RuleSource = Field(description="规则来源")
    
    # 规则条件（条件匹配时规则生效）
    condition: Optional[Dict[str, Any]] = Field(
        default=None,
        description="规则适用条件，如 {'chapter_level': 1, 'has_boq': True}"
    )
    condition_description: str = Field(description="条件的自然语言描述")
    
    # 规则内容（描述规则的实际要求）
    description: str = Field(description="规则的自然语言描述")
    pattern: Optional[str] = Field(
        default=None,
        description="规则的模式/示例，如文本、正则表达式、JSON 结构等"
    )
    
    # 规则动作（指导生成/检查如何处理）
    action: Optional[Dict[str, Any]] = Field(
        default=None,
        description="规则动作，如 {'type': 'require', 'field': 'title', 'min_length': 10}"
    )
    action_description: str = Field(description="动作的自然语言描述")
    
    # 规则约束（定量约束）
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="定量约束，如 {'min_value': 100, 'max_value': 1000, 'unit': 'words'}"
    )
    
    # 规则覆盖范围
    scope: Optional[Dict[str, Any]] = Field(
        default=None,
        description="规则适用范围，如 {'chapter_ids': [...], 'file_types': ['docx']}"
    )
    
    # 元数据
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="规则的置信度（0-1）"
    )
    version: int = Field(default=1, description="规则版本号")
    tags: List[str] = Field(default_factory=list, description="规则标签")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 参考信息（用于追踪规则来源）
    reference: Optional[Dict[str, Any]] = Field(
        default=None,
        description="参考信息，如 {'file_id': '...', 'chapter_id': '...', 'section': 'xxx'}"
    )
    
    # 检查建议（用于检查 MCP 返回违规时的修复建议）
    fix_suggestion: Optional[str] = Field(
        default=None,
        description="违规修复建议"
    )
    
    # 示例（帮助生成 MCP 理解如何应用）
    examples: Optional[List[str]] = Field(
        default=None,
        description="规则应用示例"
    )
    
    # 反例（帮助检查 MCP 识别什么是不符合的）
    counter_examples: Optional[List[str]] = Field(
        default=None,
        description="反面示例"
    )
    
    class Config:
        use_enum_values = False


class RulePackage(BaseModel):
    """
    规则包
    
    一次学习/检查/生成操作的规则集合
    """
    
    # 包的元信息
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="规则包ID")
    name: str = Field(description="规则包名称")
    description: Optional[str] = Field(default=None, description="规则包描述")
    
    # 规则集合（按类型分组）
    structure_rules: List[Rule] = Field(default_factory=list, description="结构规则")
    content_rules: List[Rule] = Field(default_factory=list, description="内容规则")
    mandatory_rules: List[Rule] = Field(default_factory=list, description="强制要求")
    scoring_rules: List[Rule] = Field(default_factory=list, description="评分规则")
    consistency_rules: List[Rule] = Field(default_factory=list, description="一致性约束")
    formatting_rules: List[Rule] = Field(default_factory=list, description="格式规范")
    terminology_rules: List[Rule] = Field(default_factory=list, description="术语规则")
    
    # 包的统计
    total_rules: int = Field(default=0, description="总规则数")
    coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="规则覆盖率（0-1）"
    )
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_rules = sum([
            len(self.structure_rules),
            len(self.content_rules),
            len(self.mandatory_rules),
            len(self.scoring_rules),
            len(self.consistency_rules),
            len(self.formatting_rules),
            len(self.terminology_rules),
        ])
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """按类型获取规则"""
        rules_map = {
            RuleType.STRUCTURE: self.structure_rules,
            RuleType.CONTENT: self.content_rules,
            RuleType.MANDATORY: self.mandatory_rules,
            RuleType.SCORING: self.scoring_rules,
            RuleType.CONSISTENCY: self.consistency_rules,
            RuleType.FORMATTING: self.formatting_rules,
            RuleType.TERMINOLOGY: self.terminology_rules,
        }
        return rules_map.get(rule_type, [])
    
    def get_rules_by_priority(self, priority: RulePriority) -> List[Rule]:
        """按优先级获取规则"""
        all_rules = (
            self.structure_rules + self.content_rules + self.mandatory_rules +
            self.scoring_rules + self.consistency_rules + self.formatting_rules +
            self.terminology_rules
        )
        return [r for r in all_rules if r.priority == priority]
    
    def add_rule(self, rule: Rule) -> None:
        """添加规则"""
        rules_map = {
            RuleType.STRUCTURE: self.structure_rules,
            RuleType.CONTENT: self.content_rules,
            RuleType.MANDATORY: self.mandatory_rules,
            RuleType.SCORING: self.scoring_rules,
            RuleType.CONSISTENCY: self.consistency_rules,
            RuleType.FORMATTING: self.formatting_rules,
            RuleType.TERMINOLOGY: self.terminology_rules,
        }
        rules_map[rule.type].append(rule)
        self.total_rules += 1


class MergeResult(BaseModel):
    """规则合并结果"""
    
    new_rules: List[Rule] = Field(description="新增规则")
    updated_rules: List[Rule] = Field(description="更新的规则")
    skipped_rules: List[Rule] = Field(description="跳过的规则（重复）")
    conflicts: List[Dict[str, Any]] = Field(description="冲突规则列表")
    
    @property
    def total_merged(self) -> int:
        return len(self.new_rules) + len(self.updated_rules)
