"""
检查报告统一格式
检查 MCP 返回的报告格式，学习 MCP 分析这个格式生成新规则
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class ViolationType(str, Enum):
    """违规类型"""
    MISSING = "missing"                      # 缺失内容
    INCORRECT = "incorrect"                  # 不符合规则
    INCONSISTENT = "inconsistent"            # 不一致
    MALFORMED = "malformed"                  # 格式错误
    WEAK = "weak"                            # 不够强（评分低）


class Severity(str, Enum):
    """严重程度"""
    CRITICAL = "critical"                    # 致命（不合格）
    WARNING = "warning"                      # 警告（扣分）
    INFO = "info"                            # 信息（参考）


class Violation(BaseModel):
    """单个违规"""
    
    id: str = Field(description="违规ID")
    rule_id: Optional[str] = Field(
        default=None,
        description="触发的规则ID"
    )
    violation_type: ViolationType = Field(description="违规类型")
    severity: Severity = Field(description="严重程度")
    
    # 违规位置
    location: Dict[str, Any] = Field(
        description="违规位置信息，如 {'chapter_id': '...', 'section': '...', 'position': 123}"
    )
    
    # 违规描述
    description: str = Field(description="违规的自然语言描述")
    
    # 期望值
    expected: Optional[str] = Field(default=None, description="期望值/内容")
    
    # 实际值
    actual: Optional[str] = Field(default=None, description="实际值/内容")
    
    # 修复建议
    fix_suggestion: Optional[str] = Field(default=None, description="修复建议")
    
    # 置信度
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="这个违规判定的置信度"
    )


class CheckResult(BaseModel):
    """单个检查项的结果"""
    
    id: str = Field(description="检查项ID")
    name: str = Field(description="检查项名称")
    description: Optional[str] = Field(default=None, description="检查项描述")
    
    # 检查结果
    passed: bool = Field(description="是否通过")
    score: float = Field(
        ge=0.0,
        le=100.0,
        description="检查得分（0-100）"
    )
    
    # 违规列表（如果有）
    violations: List[Violation] = Field(default_factory=list, description="违规列表")


class CheckReport(BaseModel):
    """
    检查报告
    
    检查 MCP 返回这个格式的报告，学习 MCP 分析并生成新规则
    """
    
    # 报告的元信息
    id: str = Field(description="报告ID")
    content_id: str = Field(description="被检查的内容ID（文件ID或章节ID）")
    check_type: str = Field(description="检查类型（'file' 或 'chapter'）")
    
    # 总体评分
    overall_score: float = Field(
        ge=0.0,
        le=100.0,
        description="总体得分"
    )
    is_qualified: bool = Field(description="是否合格（通常 >= 60 分）")
    
    # 分项检查结果
    check_results: List[CheckResult] = Field(description="检查结果列表")
    
    # 所有违规（汇总）
    total_violations: int = Field(description="总违规数")
    critical_violations: List[Violation] = Field(
        description="致命违规（必须修复）"
    )
    warning_violations: List[Violation] = Field(
        description="警告违规（建议修复）"
    )
    
    # 统计信息
    statistics: Dict[str, Any] = Field(
        description="统计信息，如 {'by_type': {...}, 'by_severity': {...}}"
    )
    
    # 建议
    recommendations: List[str] = Field(
        default_factory=list,
        description="改进建议"
    )
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="额外元数据"
    )
    
    class Config:
        use_enum_values = False
    
    def summary(self) -> str:
        """生成报告摘要"""
        return (
            f"检查报告: {self.check_type.upper()} | "
            f"得分: {self.overall_score:.0f}分 | "
            f"状态: {'✅ 合格' if self.is_qualified else '❌ 不合格'} | "
            f"违规: {self.total_violations} 项"
        )


class LearningFeedback(BaseModel):
    """
    学习反馈
    
    学习 MCP 分析检查报告后生成的新规则反馈
    """
    
    report_id: str = Field(description="源报告ID")
    
    # 新发现的规则
    new_rules: List[Dict[str, Any]] = Field(
        description="从报告中提取的新规则"
    )
    
    # 需要强化的规则
    rules_to_strengthen: List[Dict[str, Any]] = Field(
        description="需要更新/强化的现有规则"
    )
    
    # 冲突规则
    conflicting_rules: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="发现的冲突规则"
    )
    
    # 分析过程
    analysis: str = Field(
        description="分析过程的自然语言描述"
    )
    
    # 置信度
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="学习反馈的置信度"
    )
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
