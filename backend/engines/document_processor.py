"""
文件处理流程控制器
根据文件分类，采用不同的处理策略
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from core.logger import logger
from engines.smart_document_classifier import (
    SmartDocumentClassifier,
    DocumentType,
    DocumentAnalysis
)
from engines.ocr_extractor import HybridTextExtractor, DocumentImageExtractor


class FileProcessingStrategy:
    """文件处理策略基类"""
    
    def __init__(self, file_path: str, analysis: DocumentAnalysis):
        self.file_path = file_path
        self.analysis = analysis
    
    async def process(self) -> Dict:
        """处理文件，返回处理结果"""
        raise NotImplementedError


class MainProposalStrategy(FileProcessingStrategy):
    """主标书处理策略 - 提取目录和内容"""
    
    async def process(self) -> Dict:
        """
        处理主标书：
        1. 提取目录结构
        2. 提取内容
        3. 提取图片元数据（仅位置，不保存）
        """
        logger.info(f"[标书] 处理主标书: {Path(self.file_path).name}")
        
        from engines.parse_engine import ParseEngine
        
        try:
            parser = ParseEngine()
            result = parser.parse(self.file_path, "tender", save_to_db=False)
            
            return {
                'status': 'success',
                'file_type': 'main_proposal',
                'chapters': result.get('chapters', []),
                'content_length': len(result.get('content', '')),
                'processing_time': datetime.now().isoformat(),
                'note': '已提取目录和内容'
            }
        
        except Exception as e:
            logger.error(f"主标书处理失败: {e}")
            return {
                'status': 'error',
                'file_type': 'main_proposal',
                'error': str(e),
                'processing_time': datetime.now().isoformat()
            }


class ScanPDFStrategy(FileProcessingStrategy):
    """扫描PDF处理策略 - 使用OCR识别"""
    
    async def process(self) -> Dict:
        """
        处理纯扫描PDF：
        1. 使用PaddleOCR识别
        2. 提取目录结构
        3. 保存OCR结果
        """
        logger.info(f"[扫描] 处理扫描PDF: {Path(self.file_path).name}")
        
        try:
            extractor = HybridTextExtractor(use_paddle_ocr=True)
            
            # Step 1: OCR提取
            logger.info("开始OCR识别...")
            extraction_results = await extractor.extract_document(self.file_path)
            
            # Step 2: 合并文本
            full_text = '\n'.join([
                r['text'] for r in extraction_results
                if r.get('text')
            ])
            
            # Step 3: 目录提取（基于OCR结果）
            from engines.parse_engine import ParseEngine
            parser = ParseEngine()
            
            # 使用现有的章节提取逻辑
            chapters = parser._extract_from_content(full_text)
            
            ocr_methods = [r['method'] for r in extraction_results]
            ocr_confidence = sum(r['confidence'] for r in extraction_results) / len(extraction_results)
            
            return {
                'status': 'success',
                'file_type': 'scan_pdf',
                'chapters': chapters,
                'total_pages': len(extraction_results),
                'ocr_pages': sum(1 for r in extraction_results if r['method'] == 'ocr'),
                'average_confidence': ocr_confidence,
                'content_length': len(full_text),
                'processing_time': datetime.now().isoformat(),
                'note': f'使用PaddleOCR识别，置信度{ocr_confidence:.2%}'
            }
        
        except Exception as e:
            logger.error(f"扫描PDF处理失败: {e}")
            return {
                'status': 'error',
                'file_type': 'scan_pdf',
                'error': str(e),
                'processing_time': datetime.now().isoformat()
            }


class MixedPDFStrategy(FileProcessingStrategy):
    """混合PDF处理策略 - 文本+OCR混合"""
    
    async def process(self) -> Dict:
        """
        处理混合PDF：
        1. 文本页直接提取
        2. 扫描页用OCR识别
        3. 合并结果
        """
        logger.info(f"[混合] 处理混合PDF: {Path(self.file_path).name}")
        
        try:
            extractor = HybridTextExtractor(use_paddle_ocr=True)
            
            extraction_results = await extractor.extract_document(self.file_path)
            
            # 统计方法使用
            methods = {}
            for r in extraction_results:
                method = r['method']
                methods[method] = methods.get(method, 0) + 1
            
            # 合并文本
            full_text = '\n'.join([
                r['text'] for r in extraction_results
                if r.get('text')
            ])
            
            # 目录提取
            from engines.parse_engine import ParseEngine
            parser = ParseEngine()
            chapters = parser._extract_from_content(full_text)
            
            avg_confidence = sum(r['confidence'] for r in extraction_results) / len(extraction_results)
            
            return {
                'status': 'success',
                'file_type': 'mixed_pdf',
                'chapters': chapters,
                'total_pages': len(extraction_results),
                'extraction_methods': methods,
                'average_confidence': avg_confidence,
                'content_length': len(full_text),
                'processing_time': datetime.now().isoformat(),
                'note': f'混合提取: {methods.get("direct", 0)}页文本+{methods.get("ocr", 0)}页OCR'
            }
        
        except Exception as e:
            logger.error(f"混合PDF处理失败: {e}")
            return {
                'status': 'error',
                'file_type': 'mixed_pdf',
                'error': str(e),
                'processing_time': datetime.now().isoformat()
            }


class FinancialReportStrategy(FileProcessingStrategy):
    """财务报告处理策略 - 按年份分离并存档"""
    
    async def process(self) -> Dict:
        """
        处理财务报告：
        1. 按年份自动分离为独立PDF文件
        2. 存档到 /archive/financial_reports/YYYY/
        3. 不解析内容(仅OCR识别年份)
        4. 保存到financial_reports表
        """
        from engines.financial_report_splitter import FinancialReportSplitter
        
        logger.info(f"[财务] 处理财务报告: {Path(self.file_path).name}")
        
        # 生成临时file_id用于关联
        import uuid
        file_id = str(uuid.uuid4())
        
        # 分离并存档
        splitter = FinancialReportSplitter()
        archived_files = splitter.split_and_archive(self.file_path, file_id)
        
        years = [f['year'] for f in archived_files if f.get('year')]
        total_pages = sum(f['page_count'] for f in archived_files)
        
        return {
            'status': 'success',
            'file_id': file_id,
            'file_type': 'financial_report',
            'total_pages': total_pages,
            'detected_years': years,
            'archived_files': archived_files,
            'processing_strategy': 'split_and_archive',
            'processing_time': datetime.now().isoformat(),
            'note': f'财务报告已按年份分离: {years}年，共{len(archived_files)}个文件'
        }


class CertificateStrategy(FileProcessingStrategy):
    """证件/资质处理策略 - 仅记录位置和格式"""
    
    async def process(self) -> Dict:
        """
        处理证件：
        1. 不解析内容
        2. 仅记录位置、页数、格式
        3. 保存PDF文件
        """
        logger.info(f"[证件] 处理证件/资质: {Path(self.file_path).name}")
        
        return {
            'status': 'success',
            'file_type': self.analysis.file_type.value,
            'total_pages': self.analysis.total_pages,
            'scan_page_ratio': self.analysis.scan_page_ratio,
            'processing_strategy': 'store_only',
            'processing_time': datetime.now().isoformat(),
            'note': '仅保存PDF，记录位置和页数，不解析内容'
        }


class ImageStrategy(FileProcessingStrategy):
    """图片处理策略 - 仅提取元数据"""
    
    async def process(self) -> Dict:
        """
        处理图片：
        1. 提取文件元数据
        2. 不保存图片内容
        3. 记录位置和大小
        """
        logger.info(f"[图片] 处理图片: {Path(self.file_path).name}")
        
        from engines.ocr_extractor import ImageMetadataExtractor
        
        metadata = ImageMetadataExtractor.extract_metadata(self.file_path)
        
        return {
            'status': 'success',
            'file_type': 'image',
            'metadata': metadata,
            'processing_strategy': 'metadata_only',
            'processing_time': datetime.now().isoformat(),
            'note': '仅提取元数据（大小、格式等），不保存图片'
        }


class DocumentProcessor:
    """文件处理器 - 根据分类选择策略"""
    
    def __init__(self):
        self.classifier = SmartDocumentClassifier()
    
    async def process(self, file_path: str, filename: str) -> Dict:
        """
        处理文件
        
        Args:
            file_path: 文件完整路径
            filename: 文件名
            
        Returns:
            处理结果
        """
        # Step 1: 分类
        logger.info(f"开始文件处理: {filename}")
        analysis = self.classifier.classify(file_path, filename)
        
        logger.info(f"文件分类: {analysis.file_type.value}")
        logger.info(f"处理策略: {analysis.processing_strategy}")
        logger.info(f"处理说明: {analysis.processing_note}")
        
        # Step 2: 选择策略
        strategy_map = {
            DocumentType.MAIN_PROPOSAL: MainProposalStrategy,
            DocumentType.SCAN_PDF: ScanPDFStrategy,
            DocumentType.MIXED_PDF: MixedPDFStrategy,
            DocumentType.FINANCIAL_REPORT: FinancialReportStrategy,
            DocumentType.PERFORMANCE_REPORT: CertificateStrategy,
            DocumentType.LICENSE: CertificateStrategy,
            DocumentType.CERTIFICATE: CertificateStrategy,
            DocumentType.IMAGE_ONLY: ImageStrategy,
        }
        
        strategy_class = strategy_map.get(analysis.file_type)
        
        if strategy_class is None:
            logger.warning(f"无处理策略: {analysis.file_type.value}")
            return {
                'status': 'skip',
                'file_type': analysis.file_type.value,
                'reason': '不支持的文件类型'
            }
        
        # Step 3: 执行策略
        strategy = strategy_class(file_path, analysis)
        result = await strategy.process()
        
        # 添加分类信息
        result['classification'] = analysis.to_dict()
        
        return result
