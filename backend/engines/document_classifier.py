"""
文档分类引擎
根据文件名和解析内容自动分类文档
"""
import os
import re
from typing import Dict, Tuple
from datetime import datetime
from core.logger import logger
from core.file_status import FileCategory


class DocumentClassifier:
    """
    文档智能分类器
    - 根据文件名准确性选择快速/详细分析策略
    - 自动生成语义化文件名
    """
    
    # 文件名准确性评估关键词
    ACCURATE_PATTERNS = [
        r'\d{4}年.*?招标',
        r'.*?项目.*?投标',
        r'招标文件',
        r'投标书',
        r'技术方案',
        r'商务报价',
        r'合同',
        r'协议',
    ]
    
    # 分类关键词（用于快速分析）
    CATEGORY_KEYWORDS = {
        FileCategory.TENDER: [
            '招标', '招标文件', '招标公告', '投标须知', '评分标准', 
            '技术规格书', '招标要求', '资格预审'
        ],
        FileCategory.PROPOSAL: [
            '投标', '投标书', '投标文件', '技术方案', '商务报价', 
            '投标函', '报价单', '技术标', '商务标'
        ],
        FileCategory.CONTRACT: [
            '合同', '协议', '合同书', '协议书', '采购合同', '服务协议'
        ],
        FileCategory.REPORT: [
            '报告', '总结', '分析报告', '项目报告', '评估报告', '调研报告'
        ],
        FileCategory.REFERENCE: [
            '参考', '资料', '文档', '说明', '手册', '指南'
        ],
    }
    
    def __init__(self):
        self.logger = logger
    
    def is_filename_accurate(self, filename: str) -> bool:
        """
        判断文件名是否准确（包含明确的项目/类型信息）
        
        Args:
            filename: 文件名
            
        Returns:
            bool: True=文件名准确，False=文件名模糊
        """
        # 移除扩展名
        name_without_ext = os.path.splitext(filename)[0]
        
        # 检查是否匹配准确模式
        for pattern in self.ACCURATE_PATTERNS:
            if re.search(pattern, name_without_ext):
                return True
        
        # 检查是否包含日期+描述性文字
        has_date = bool(re.search(r'\d{4}[-年]\d{1,2}[-月]\d{1,2}', name_without_ext))
        has_description = len(name_without_ext) > 10  # 描述性文件名通常较长
        
        if has_date and has_description:
            return True
        
        return False
    
    def quick_classify(self, filename: str, content: str = None) -> FileCategory:
        """
        快速分类（用于文件名准确的情况）
        主要基于文件名关键词匹配
        
        Args:
            filename: 文件名
            content: 文件内容（可选，用于辅助判断）
            
        Returns:
            FileCategory: 文档分类
        """
        text = filename
        if content:
            # 只取前500字进行快速分析
            text = filename + " " + content[:500]
        
        text = text.lower()
        
        # 关键词匹配
        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            # 返回得分最高的分类
            return max(category_scores, key=category_scores.get)
        
        return FileCategory.OTHER
    
    def detailed_classify(self, filename: str, metadata: Dict, content: str) -> FileCategory:
        """
        详细分类（用于文件名模糊的情况）
        综合文件名、元数据、内容进行深度分析
        
        Args:
            filename: 文件名
            metadata: 解析的元数据
            content: 文件内容
            
        Returns:
            FileCategory: 文档分类
        """
        # 1. 文件名分析
        filename_category = self.quick_classify(filename)
        
        # 2. 内容分析（前2000字）
        content_sample = content[:2000] if content else ""
        content_category = self.quick_classify("", content_sample)
        
        # 3. 结构特征分析
        structure_category = self._analyze_structure(metadata)
        
        # 4. 综合判断
        categories = [filename_category, content_category, structure_category]
        
        # 投票机制：选择出现次数最多的分类
        from collections import Counter
        counter = Counter(categories)
        most_common = counter.most_common(1)[0][0]
        
        self.logger.info(
            f"详细分析完成 - 文件: {filename}, "
            f"文件名分类: {filename_category}, "
            f"内容分类: {content_category}, "
            f"结构分类: {structure_category}, "
            f"最终分类: {most_common}"
        )
        
        return most_common
    
    def _analyze_structure(self, metadata: Dict) -> FileCategory:
        """
        根据文档结构特征分析分类
        
        Args:
            metadata: 文档元数据
            
        Returns:
            FileCategory: 分类结果
        """
        # 检查是否有特定章节结构
        chapters = metadata.get('chapters', [])
        chapter_titles = [ch.get('title', '') for ch in chapters]
        all_titles = " ".join(chapter_titles)
        
        # 招标文件通常包含特定章节
        if any(kw in all_titles for kw in ['投标须知', '评分标准', '技术规格']):
            return FileCategory.TENDER
        
        # 投标文件通常包含特定章节
        if any(kw in all_titles for kw in ['技术方案', '商务报价', '投标函']):
            return FileCategory.PROPOSAL
        
        # 合同文件特征
        if any(kw in all_titles for kw in ['甲方', '乙方', '合同条款', '违约责任']):
            return FileCategory.CONTRACT
        
        return FileCategory.OTHER
    
    def generate_semantic_filename(
        self, 
        original_filename: str,
        category: FileCategory,
        metadata: Dict,
        content: str = None
    ) -> str:
        """
        生成语义化文件名
        
        格式: {日期}_{项目名}_{文档类型}_{版本}.{扩展名}
        示例: 2025-12-07_某某系统集成项目_招标文件_v1.0.pdf
        
        Args:
            original_filename: 原始文件名
            category: 文档分类
            metadata: 元数据
            content: 内容（可选）
            
        Returns:
            str: 语义化文件名
        """
        # 1. 提取扩展名
        _, ext = os.path.splitext(original_filename)
        
        # 2. 提取/生成日期
        date_str = self._extract_date(original_filename, metadata, content)
        
        # 3. 提取项目名称
        project_name = self._extract_project_name(original_filename, metadata, content)
        
        # 4. 文档类型
        doc_type = self._get_doc_type_label(category)
        
        # 5. 版本号（如果有）
        version = self._extract_version(original_filename, metadata)
        
        # 6. 组合文件名
        parts = [date_str, project_name, doc_type]
        if version:
            parts.append(version)
        
        semantic_name = "_".join(filter(None, parts)) + ext
        
        # 7. 清理文件名（移除非法字符）
        semantic_name = re.sub(r'[<>:"/\\|?*]', '', semantic_name)
        
        return semantic_name
    
    def _extract_date(self, filename: str, metadata: Dict, content: str = None) -> str:
        """提取日期"""
        # 优先从文件名提取
        date_match = re.search(r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})', filename)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # 从元数据提取
        if 'date' in metadata:
            return metadata['date']
        
        # 使用当前日期
        return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_project_name(self, filename: str, metadata: Dict, content: str = None) -> str:
        """提取项目名称"""
        # 从文件名提取
        # 匹配如: "XX项目", "XX系统", "XX工程"
        match = re.search(r'([^_\-\s]{2,20}(?:项目|系统|工程|平台|建设))', filename)
        if match:
            return match.group(1)
        
        # 从元数据提取
        if 'project_name' in metadata:
            return metadata['project_name']
        
        # 从内容前100字提取
        if content:
            match = re.search(r'([^，。；]{2,20}(?:项目|系统|工程|平台|建设))', content[:100])
            if match:
                return match.group(1)
        
        return "未命名项目"
    
    def _get_doc_type_label(self, category: FileCategory) -> str:
        """获取文档类型标签"""
        labels = {
            FileCategory.TENDER: "招标文件",
            FileCategory.PROPOSAL: "投标文件",
            FileCategory.CONTRACT: "合同文件",
            FileCategory.REPORT: "报告文档",
            FileCategory.REFERENCE: "参考资料",
            FileCategory.OTHER: "其他文档",
        }
        return labels.get(category, "文档")
    
    def _extract_version(self, filename: str, metadata: Dict) -> str:
        """提取版本号"""
        # 从文件名提取
        version_match = re.search(r'[vV](\d+\.?\d*)', filename)
        if version_match:
            return f"v{version_match.group(1)}"
        
        # 从元数据提取
        if 'version' in metadata:
            return f"v{metadata['version']}"
        
        return ""
    
    def classify(
        self, 
        filename: str, 
        metadata: Dict = None, 
        content: str = None
    ) -> Tuple[FileCategory, str]:
        """
        分类主入口
        自动选择快速/详细分析策略
        
        Args:
            filename: 文件名
            metadata: 元数据（可选）
            content: 内容（可选）
            
        Returns:
            Tuple[FileCategory, str]: (分类结果, 语义化文件名)
        """
        is_accurate = self.is_filename_accurate(filename)
        
        if is_accurate:
            # 文件名准确：快速分类
            self.logger.info(f"文件名准确，使用快速分析: {filename}")
            category = self.quick_classify(filename, content)
        else:
            # 文件名模糊：详细分类
            self.logger.info(f"文件名模糊，使用详细分析: {filename}")
            if not metadata or not content:
                self.logger.warning(f"详细分析需要元数据和内容，降级为快速分析: {filename}")
                category = self.quick_classify(filename, content)
            else:
                category = self.detailed_classify(filename, metadata, content)
        
        # 生成语义化文件名
        semantic_name = self.generate_semantic_filename(
            filename, 
            category, 
            metadata or {}, 
            content
        )
        
        return category, semantic_name
