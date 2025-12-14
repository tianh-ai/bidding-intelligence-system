"""
文件分类和智能处理引擎
处理不同类型的投标文件：目录文件、图片文件、证件、财务报告等

关键处理逻辑：
1. 证件类（营业执照、资质证书等）：仅提取位置和格式，不解析内容
2. 财务报告（多页）：按年份分组，直接存储为PDF，不解析
3. 业绩报告：仅记录位置和页数，不详细解析
4. 扫描PDF：使用OCR识别
5. 普通文本PDF：正常解析目录和内容
6. 图片：仅提取元数据（位置、大小等）
"""

import re
import json
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from core.logger import logger


class DocumentType(Enum):
    """文件类型枚举"""
    # 主要文件
    MAIN_PROPOSAL = "main_proposal"              # 主标书（可解析）
    
    # 证件类（仅记录位置）
    LICENSE = "license"                          # 营业执照
    CERTIFICATE = "certificate"                  # 资质证书
    ID_CARD = "id_card"                          # 身份证
    QUALIFICATION = "qualification"              # 从业资格
    
    # 报告类（按特殊规则处理）
    FINANCIAL_REPORT = "financial_report"        # 财务报告
    PERFORMANCE_REPORT = "performance_report"    # 业绩报告
    AUDIT_REPORT = "audit_report"                # 审计报告
    
    # PDF类型
    SCAN_PDF = "scan_pdf"                        # 纯扫描PDF（需OCR）
    MIXED_PDF = "mixed_pdf"                      # 混合PDF
    
    # 其他
    IMAGE_ONLY = "image_only"                    # 单个图片
    UNKNOWN = "unknown"                          # 未知


class PageType(Enum):
    """页面类型"""
    TEXT_PAGE = "text"
    SCAN_PAGE = "scan"
    IMAGE_PAGE = "image"
    BLANK_PAGE = "blank"
    MIXED_PAGE = "mixed"


@dataclass
class PageAnalysis:
    """页面分析结果"""
    page_num: int
    page_type: PageType
    text_density: float
    image_count: int
    image_ratio: float                           # 图片面积占比
    has_table: bool
    confidence: float = 0.0


@dataclass
class DocumentAnalysis:
    """文件分析结果"""
    file_path: str
    file_type: DocumentType
    total_pages: int
    page_analyses: List[PageAnalysis]
    
    # 统计
    scan_page_ratio: float
    image_page_ratio: float
    text_page_ratio: float
    
    # 特殊属性
    is_financial_report: bool = False
    financial_years: List[int] = None
    detected_documents: Dict[str, int] = None    # {'财务报告2023': 12, '业绩报告': 8}
    
    confidence: float = 0.0
    processing_strategy: str = ""
    processing_note: str = ""
    
    def to_dict(self):
        return {
            'file_path': self.file_path,
            'file_type': self.file_type.value,
            'total_pages': self.total_pages,
            'scan_page_ratio': self.scan_page_ratio,
            'image_page_ratio': self.image_page_ratio,
            'text_page_ratio': self.text_page_ratio,
            'is_financial_report': self.is_financial_report,
            'financial_years': self.financial_years,
            'detected_documents': self.detected_documents,
            'processing_strategy': self.processing_strategy,
            'processing_note': self.processing_note
        }


class SmartDocumentClassifier:
    """智能文件分类器"""
    
    # 证件关键词
    LICENSE_KEYWORDS = ['营业执照', '工商', '注册号', '统一社会信用', 'license']
    CERT_KEYWORDS = ['资质', '证书', '认证', 'certificate', '许可证', '等级']
    
    # 财务报告关键词
    FINANCIAL_KEYWORDS = ['财务报表', '资产负债表', '利润表', '现金流量表', '财务报告', '年报', 'financial']
    PERFORMANCE_KEYWORDS = ['业绩', '工程', '施工', '项目完成', '中标', 'performance']
    
    # 年份模式
    YEAR_PATTERN = re.compile(r'(19|20)\d{2}|(\d{4})年|(\d{4}年度)')
    
    def __init__(self):
        self.ocr_engine = None  # 延迟初始化
    
    def classify(self, file_path: str, filename: str) -> DocumentAnalysis:
        """
        分类文件并确定处理策略
        """
        from pypdf import PdfReader
        
        ext = Path(filename).suffix.lower()
        
        # 图片文件
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.IMAGE_ONLY,
                total_pages=1,
                page_analyses=[],
                scan_page_ratio=0,
                image_page_ratio=1.0,
                text_page_ratio=0,
                confidence=1.0,
                processing_strategy='extract_metadata',
                processing_note='图片文件，仅提取位置和大小'
            )
        
        # Word文档
        if ext == '.docx':
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.MAIN_PROPOSAL,
                total_pages=0,
                page_analyses=[],
                scan_page_ratio=0,
                image_page_ratio=0,
                text_page_ratio=1.0,
                confidence=1.0,
                processing_strategy='extract_text_word',
                processing_note='Word文档，使用python-docx提取'
            )
        
        # PDF处理
        if ext != '.pdf':
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.UNKNOWN,
                total_pages=0,
                page_analyses=[],
                scan_page_ratio=0,
                image_page_ratio=0,
                text_page_ratio=0,
                confidence=0.0,
                processing_strategy='skip',
                processing_note='不支持的文件类型'
            )
        
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            
            # 分析前20页
            page_analyses = []
            for i in range(min(20, total_pages)):
                analysis = self._analyze_page(reader.pages[i], i)
                page_analyses.append(analysis)
            
            # 获取首页文本用于分类
            first_text = ""
            try:
                first_text = reader.pages[0].extract_text() or ""
            except:
                pass
            
            return self._determine_type(
                file_path, filename, total_pages,
                page_analyses, first_text
            )
        
        except Exception as e:
            logger.error(f"文件分析失败 {filename}: {e}")
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.UNKNOWN,
                total_pages=0,
                page_analyses=[],
                scan_page_ratio=0,
                image_page_ratio=0,
                text_page_ratio=0,
                confidence=0.0,
                processing_strategy='error',
                processing_note=f'分析失败: {str(e)}'
            )
    
    def _analyze_page(self, page, page_num: int) -> PageAnalysis:
        """分析页面类型"""
        try:
            text = page.extract_text() or ""
            images = page.images
            
            text_len = len(text.strip())
            image_count = len(images)
            
            # 估算图片面积占比（简化）
            image_ratio = 0.7 if image_count > 2 else (0.3 if image_count > 0 else 0)
            
            # 判断页面类型
            if text_len < 50 and image_count == 0:
                page_type = PageType.BLANK_PAGE
            elif text_len > 500 and image_ratio < 0.2:
                page_type = PageType.TEXT_PAGE
            elif image_ratio > 0.7 and text_len < 100:
                page_type = PageType.SCAN_PAGE
            elif image_count > 0:
                page_type = PageType.MIXED_PAGE if text_len > 100 else PageType.IMAGE_PAGE
            else:
                page_type = PageType.TEXT_PAGE
            
            return PageAnalysis(
                page_num=page_num,
                page_type=page_type,
                text_density=min(text_len / 2000, 1.0),
                image_count=image_count,
                image_ratio=image_ratio,
                has_table=False,
                confidence=0.8
            )
        except:
            return PageAnalysis(
                page_num=page_num,
                page_type=PageType.BLANK_PAGE,
                text_density=0,
                image_count=0,
                image_ratio=0,
                has_table=False,
                confidence=0.0
            )
    
    def _determine_type(
        self,
        file_path: str,
        filename: str,
        total_pages: int,
        page_analyses: List[PageAnalysis],
        first_text: str
    ) -> DocumentAnalysis:
        """确定文件类型和处理策略"""
        
        # 统计
        scan_count = sum(1 for p in page_analyses if p.page_type == PageType.SCAN_PAGE)
        text_count = sum(1 for p in page_analyses if p.page_type == PageType.TEXT_PAGE)
        analyzed = len(page_analyses)
        
        scan_ratio = scan_count / analyzed if analyzed > 0 else 0
        text_ratio = text_count / analyzed if analyzed > 0 else 0
        
        # 分类规则
        
        # 1. 检查证件
        if self._is_certificate(first_text, filename):
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.LICENSE,
                total_pages=total_pages,
                page_analyses=page_analyses,
                scan_page_ratio=scan_ratio,
                image_page_ratio=1.0 - text_ratio,
                text_page_ratio=text_ratio,
                confidence=0.9,
                processing_strategy='store_pdf_only',
                processing_note='证件/资质文件，仅存储，记录位置'
            )
        
        # 2. 检查财务报告
        if self._is_financial_report(first_text, filename, total_pages):
            years = self._extract_years(first_text)
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.FINANCIAL_REPORT,
                total_pages=total_pages,
                page_analyses=page_analyses,
                scan_page_ratio=scan_ratio,
                image_page_ratio=1.0 - text_ratio,
                text_page_ratio=text_ratio,
                is_financial_report=True,
                financial_years=years,
                confidence=0.85,
                processing_strategy='group_by_year_store',
                processing_note=f'财务报告 {years}，按年份分组存储，不解析'
            )
        
        # 3. 检查业绩报告
        if self._is_performance_report(first_text, filename):
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.PERFORMANCE_REPORT,
                total_pages=total_pages,
                page_analyses=page_analyses,
                scan_page_ratio=scan_ratio,
                image_page_ratio=1.0 - text_ratio,
                text_page_ratio=text_ratio,
                confidence=0.8,
                processing_strategy='store_pdf_only',
                processing_note='业绩/扫描报告，仅存储，记录位置和页数'
            )
        
        # 4. 纯扫描PDF
        if scan_ratio > 0.8:
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.SCAN_PDF,
                total_pages=total_pages,
                page_analyses=page_analyses,
                scan_page_ratio=scan_ratio,
                image_page_ratio=1.0 - text_ratio,
                text_page_ratio=text_ratio,
                confidence=0.85,
                processing_strategy='ocr_then_parse',
                processing_note=f'纯扫描PDF，使用PaddleOCR识别'
            )
        
        # 5. 混合PDF
        if scan_ratio > 0.2:
            return DocumentAnalysis(
                file_path=file_path,
                file_type=DocumentType.MIXED_PDF,
                total_pages=total_pages,
                page_analyses=page_analyses,
                scan_page_ratio=scan_ratio,
                image_page_ratio=1.0 - text_ratio,
                text_page_ratio=text_ratio,
                confidence=0.8,
                processing_strategy='hybrid_parse',
                processing_note=f'混合PDF：{text_count}页文本+{scan_count}页扫描'
            )
        
        # 6. 默认：普通文本PDF（主标书）
        return DocumentAnalysis(
            file_path=file_path,
            file_type=DocumentType.MAIN_PROPOSAL,
            total_pages=total_pages,
            page_analyses=page_analyses,
            scan_page_ratio=scan_ratio,
            image_page_ratio=1.0 - text_ratio,
            text_page_ratio=text_ratio,
            confidence=0.9,
            processing_strategy='extract_toc_and_content',
            processing_note='主标书文件，提取目录和内容'
        )
    
    def _is_certificate(self, text: str, filename: str) -> bool:
        """检查是否证件类"""
        for kw in self.LICENSE_KEYWORDS + self.CERT_KEYWORDS:
            if kw in text or kw in filename:
                return True
        return False
    
    def _is_financial_report(self, text: str, filename: str, total_pages: int) -> bool:
        """检查是否财务报告"""
        if total_pages < 5:  # 财务报告通常多页
            return False
        
        for kw in self.FINANCIAL_KEYWORDS:
            if kw in text or kw in filename:
                return True
        
        return False
    
    def _is_performance_report(self, text: str, filename: str) -> bool:
        """检查是否业绩报告"""
        for kw in self.PERFORMANCE_KEYWORDS:
            if kw in text or kw in filename:
                return True
        return False
    
    def _extract_years(self, text: str) -> List[int]:
        """提取年份"""
        years = set()
        for match in self.YEAR_PATTERN.finditer(text):
            year_str = match.group(1) or match.group(2) or match.group(3)
            if year_str:
                year_str = year_str.replace('年', '').replace('年度', '')
                try:
                    year = int(year_str)
                    if 1900 < year < 2100:
                        years.add(year)
                except:
                    pass
        return sorted(list(years), reverse=True)
