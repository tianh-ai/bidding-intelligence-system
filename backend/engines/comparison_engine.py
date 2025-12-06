"""
对比分析引擎 (Comparison Engine)
文档差异分析、相似度计算、热力图数据生成
"""

from typing import Dict, List, Optional, Tuple, Set
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from difflib import SequenceMatcher
from core.logger import logger


class DifferenceType(str, Enum):
    """差异类型"""
    ADDITION = "addition"  # 新增
    DELETION = "deletion"  # 删除
    MODIFICATION = "modification"  # 修改
    REORDER = "reorder"  # 重排


class SimilarityLevel(str, Enum):
    """相似度等级"""
    IDENTICAL = "identical"  # 完全相同 (95-100%)
    VERY_SIMILAR = "very_similar"  # 非常相似 (80-94%)
    SIMILAR = "similar"  # 相似 (60-79%)
    SOMEWHAT_SIMILAR = "somewhat_similar"  # 有些相似 (40-59%)
    DIFFERENT = "different"  # 不同 (0-39%)


class DifferencePair(BaseModel):
    """差异对"""
    diff_id: str = Field(..., description="差异ID")
    position: int = Field(..., description="位置")
    type: DifferenceType = Field(..., description="差异类型")
    doc1_content: Optional[str] = Field(None, description="文档1内容")
    doc2_content: Optional[str] = Field(None, description="文档2内容")
    context: str = Field(..., description="上下文")
    severity: str = Field(..., description="严重程度：critical/important/minor")


class SectionComparison(BaseModel):
    """章节对比"""
    section_id: str = Field(..., description="章节ID")
    section_name: str = Field(..., description="章节名称")
    similarity: float = Field(..., ge=0, le=100, description="相似度 0-100")
    similarity_level: SimilarityLevel = Field(..., description="相似度等级")
    differences: List[DifferencePair] = Field(..., description="差异列表")
    doc1_word_count: int = Field(..., description="文档1字数")
    doc2_word_count: int = Field(..., description="文档2字数")
    word_count_change: int = Field(..., description="字数变化")


class DocumentComparison(BaseModel):
    """文档对比结果"""
    comparison_id: str = Field(..., description="对比ID")
    doc1_id: str = Field(..., description="文档1 ID")
    doc2_id: str = Field(..., description="文档2 ID")
    overall_similarity: float = Field(..., ge=0, le=100, description="总体相似度")
    similarity_level: SimilarityLevel = Field(..., description="相似度等级")
    section_comparisons: List[SectionComparison] = Field(..., description="章节对比")
    total_differences: int = Field(..., description="总差异数")
    difference_breakdown: Dict = Field(..., description="差异分类统计")
    total_word_count_change: int = Field(..., description="总字数变化")
    heatmap_data: Dict = Field(..., description="热力图数据")
    comparison_time: datetime = Field(default_factory=datetime.now)


class ComparisonSummary(BaseModel):
    """对比总结"""
    key_changes: List[str] = Field(..., description="关键变化")
    change_impact: Dict = Field(..., description="变化影响分析")
    recommendations: List[str] = Field(..., description="建议")


class ComparisonEngine:
    """
    对比分析引擎
    
    功能：
    - 文件差异检测与分析
    - 相似度计算
    - 差异热力图生成
    - 对标分析报告
    """
    
    def __init__(self):
        """初始化对比引擎"""
        logger.info("ComparisonEngine initialized")
        self.comparison_history: List[DocumentComparison] = []
    
    async def compare_documents(
        self,
        doc1_id: str,
        doc1_content: Dict,
        doc2_id: str,
        doc2_content: Dict,
        detailed: bool = True
    ) -> DocumentComparison:
        """
        对比两份文档
        
        Args:
            doc1_id: 文档1 ID
            doc1_content: 文档1内容
            doc2_id: 文档2 ID
            doc2_content: 文档2内容
            detailed: 是否详细对比
            
        Returns:
            对比结果
        """
        logger.info(
            f"Comparing documents {doc1_id} vs {doc2_id}",
            extra={"detailed": detailed}
        )
        
        comparison_id = f"cmp_{doc1_id}_{doc2_id}_{datetime.now().timestamp()}"
        
        # 提取章节信息
        sections1 = doc1_content.get("sections", {})
        sections2 = doc2_content.get("sections", {})
        
        # 对比各章节
        section_comparisons: List[SectionComparison] = []
        
        all_section_ids = set(sections1.keys()) | set(sections2.keys())
        
        for section_id in all_section_ids:
            section_comp = await self._compare_sections(
                section_id,
                sections1.get(section_id, {}),
                sections2.get(section_id, {}),
                detailed
            )
            section_comparisons.append(section_comp)
        
        # 计算总体相似度
        overall_similarity = (
            sum(sc.similarity for sc in section_comparisons) / len(section_comparisons)
            if section_comparisons else 0
        )
        
        similarity_level = self._get_similarity_level(overall_similarity)
        
        # 统计差异
        total_differences = sum(len(sc.differences) for sc in section_comparisons)
        
        difference_breakdown = self._analyze_differences(section_comparisons)
        
        # 计算字数变化
        total_word_count_1 = sum(sc.doc1_word_count for sc in section_comparisons)
        total_word_count_2 = sum(sc.doc2_word_count for sc in section_comparisons)
        total_word_count_change = total_word_count_2 - total_word_count_1
        
        # 生成热力图数据
        heatmap_data = self._generate_heatmap_data(section_comparisons)
        
        # 创建对比结果
        comparison = DocumentComparison(
            comparison_id=comparison_id,
            doc1_id=doc1_id,
            doc2_id=doc2_id,
            overall_similarity=overall_similarity,
            similarity_level=similarity_level,
            section_comparisons=section_comparisons,
            total_differences=total_differences,
            difference_breakdown=difference_breakdown,
            total_word_count_change=total_word_count_change,
            heatmap_data=heatmap_data
        )
        
        # 保存到历史
        self.comparison_history.append(comparison)
        
        logger.info(
            f"Documents compared",
            extra={
                "comparison_id": comparison_id,
                "overall_similarity": overall_similarity,
                "total_differences": total_differences,
                "word_count_change": total_word_count_change
            }
        )
        
        return comparison
    
    async def _compare_sections(
        self,
        section_id: str,
        section1: Dict,
        section2: Dict,
        detailed: bool
    ) -> SectionComparison:
        """对比单个章节"""
        # 获取章节内容
        content1 = section1.get("content", "")
        content2 = section2.get("content", "")
        
        # 计算相似度
        similarity = self._calculate_similarity(content1, content2)
        similarity_level = self._get_similarity_level(similarity)
        
        # 检测差异
        differences: List[DifferencePair] = []
        if detailed:
            differences = await self._detect_differences(
                content1, content2, section_id
            )
        
        # 字数统计
        doc1_word_count = len(content1.split())
        doc2_word_count = len(content2.split())
        word_count_change = doc2_word_count - doc1_word_count
        
        section_comp = SectionComparison(
            section_id=section_id,
            section_name=section1.get("name", f"Section {section_id}"),
            similarity=similarity,
            similarity_level=similarity_level,
            differences=differences,
            doc1_word_count=doc1_word_count,
            doc2_word_count=doc2_word_count,
            word_count_change=word_count_change
        )
        
        return section_comp
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（使用 SequenceMatcher）"""
        if not text1 and not text2:
            return 100.0
        if not text1 or not text2:
            return 0.0
        
        # 将文本分解为行或句子
        lines1 = text1.split('\n')
        lines2 = text2.split('\n')
        
        # 使用 SequenceMatcher 计算相似度
        matcher = SequenceMatcher(None, lines1, lines2)
        similarity = matcher.ratio() * 100
        
        return similarity
    
    async def _detect_differences(
        self,
        content1: str,
        content2: str,
        section_id: str
    ) -> List[DifferencePair]:
        """检测差异"""
        differences: List[DifferencePair] = []
        
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        
        # 使用 SequenceMatcher 找出差异
        matcher = SequenceMatcher(None, lines1, lines2)
        
        diff_position = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                diff_type = DifferenceType.MODIFICATION
                severity = "important"
            elif tag == 'delete':
                diff_type = DifferenceType.DELETION
                severity = "minor"
            elif tag == 'insert':
                diff_type = DifferenceType.ADDITION
                severity = "important"
            else:
                continue
            
            doc1_content = '\n'.join(lines1[i1:i2]) if i1 < i2 else None
            doc2_content = '\n'.join(lines2[j1:j2]) if j1 < j2 else None
            
            # 获取上下文（前后各一行）
            context_start = max(0, i1 - 1)
            context_end = min(len(lines1), i2 + 1)
            context = '\n'.join(lines1[context_start:context_end])
            
            diff = DifferencePair(
                diff_id=f"diff_{section_id}_{diff_position}",
                position=i1,
                type=diff_type,
                doc1_content=doc1_content,
                doc2_content=doc2_content,
                context=context,
                severity=severity
            )
            differences.append(diff)
            diff_position += 1
        
        return differences[:50]  # 限制返回前50个差异
    
    def _get_similarity_level(self, similarity: float) -> SimilarityLevel:
        """根据相似度返回等级"""
        if similarity >= 95:
            return SimilarityLevel.IDENTICAL
        elif similarity >= 80:
            return SimilarityLevel.VERY_SIMILAR
        elif similarity >= 60:
            return SimilarityLevel.SIMILAR
        elif similarity >= 40:
            return SimilarityLevel.SOMEWHAT_SIMILAR
        else:
            return SimilarityLevel.DIFFERENT
    
    def _analyze_differences(
        self,
        section_comparisons: List[SectionComparison]
    ) -> Dict:
        """分析差异分类"""
        breakdown = {
            "addition": 0,
            "deletion": 0,
            "modification": 0,
            "reorder": 0,
            "critical": 0,
            "important": 0,
            "minor": 0
        }
        
        for section in section_comparisons:
            for diff in section.differences:
                breakdown[diff.type.value] = breakdown.get(diff.type.value, 0) + 1
                breakdown[diff.severity] = breakdown.get(diff.severity, 0) + 1
        
        return breakdown
    
    def _generate_heatmap_data(
        self,
        section_comparisons: List[SectionComparison]
    ) -> Dict:
        """生成热力图数据"""
        heatmap = {
            "sections": [],
            "legend": {
                "100": "完全相同",
                "80-99": "非常相似",
                "60-79": "相似",
                "40-59": "有些相似",
                "0-39": "不同"
            }
        }
        
        for section in section_comparisons:
            section_heat = {
                "name": section.section_name,
                "similarity": section.similarity,
                "color": self._get_heatmap_color(section.similarity),
                "differences": len(section.differences),
                "word_count_change": section.word_count_change
            }
            heatmap["sections"].append(section_heat)
        
        return heatmap
    
    def _get_heatmap_color(self, similarity: float) -> str:
        """根据相似度返回热力图颜色"""
        if similarity >= 95:
            return "#008000"  # 绿色（完全相同）
        elif similarity >= 80:
            return "#90EE90"  # 浅绿色（非常相似）
        elif similarity >= 60:
            return "#FFFF00"  # 黄色（相似）
        elif similarity >= 40:
            return "#FFA500"  # 橙色（有些相似）
        else:
            return "#FF0000"  # 红色（不同）
    
    async def get_comparison_summary(
        self,
        comparison_id: str
    ) -> ComparisonSummary:
        """获取对比总结"""
        comparison = next(
            (c for c in self.comparison_history if c.comparison_id == comparison_id),
            None
        )
        
        if not comparison:
            logger.error(f"Comparison {comparison_id} not found")
            raise ValueError("Comparison not found")
        
        # 识别关键变化
        key_changes = []
        for section in comparison.section_comparisons:
            if section.similarity < 80:  # 不太相似的章节
                key_changes.append(
                    f"章节 '{section.section_name}' 相似度为 {section.similarity:.1f}%，存在重大差异"
                )
            
            # 字数有显著变化
            if abs(section.word_count_change) > 500:
                key_changes.append(
                    f"章节 '{section.section_name}' 字数变化 {section.word_count_change:+d} 字"
                )
        
        # 分析变化影响
        change_impact = {
            "addition_count": comparison.difference_breakdown.get("addition", 0),
            "deletion_count": comparison.difference_breakdown.get("deletion", 0),
            "modification_count": comparison.difference_breakdown.get("modification", 0),
            "total_word_change": comparison.total_word_count_change,
            "critical_issues": comparison.difference_breakdown.get("critical", 0)
        }
        
        # 生成建议
        recommendations = []
        
        if comparison.overall_similarity < 60:
            recommendations.append("文档差异较大，建议重点审查变化内容")
        
        if comparison.difference_breakdown.get("critical", 0) > 0:
            recommendations.append("存在关键变化，需要详细分析影响范围")
        
        if comparison.total_word_count_change > 2000:
            recommendations.append("内容增加显著，注意质量不要下降")
        elif comparison.total_word_count_change < -1000:
            recommendations.append("内容删除较多，确保未遗漏重要信息")
        
        summary = ComparisonSummary(
            key_changes=key_changes,
            change_impact=change_impact,
            recommendations=recommendations
        )
        
        return summary
    
    async def get_comparison_history(
        self,
        limit: int = 10
    ) -> List[Dict]:
        """获取对比历史"""
        return [
            {
                "comparison_id": c.comparison_id,
                "doc1_id": c.doc1_id,
                "doc2_id": c.doc2_id,
                "overall_similarity": c.overall_similarity,
                "similarity_level": c.similarity_level.value,
                "total_differences": c.total_differences,
                "comparison_time": c.comparison_time.isoformat()
            }
            for c in self.comparison_history[-limit:]
        ]

