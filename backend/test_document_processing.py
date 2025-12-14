#!/usr/bin/env python3
"""
综合测试：文档分类、OCR 提取、处理流程
用于验证新增的文档处理系统
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入新模块
try:
    from engines.smart_document_classifier import SmartDocumentClassifier, DocumentType
    from engines.ocr_extractor import (
        HybridTextExtractor, 
        DirectTextExtractor,
        ImageMetadataExtractor
    )
    from engines.document_processor import DocumentProcessor
    logger.info("✅ 成功导入所有新模块")
except ImportError as e:
    logger.error(f"❌ 导入失败: {e}")
    sys.exit(1)


class DocumentProcessingTest:
    """文档处理系统综合测试"""
    
    def __init__(self):
        self.classifier = SmartDocumentClassifier()
        self.processor = DocumentProcessor()
        self.test_results = []
    
    async def test_classifier(self, file_path: str, expected_type: DocumentType = None):
        """测试文档分类器"""
        logger.info(f"\n📋 测试分类: {Path(file_path).name}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            analysis = self.classifier.classify(file_path, Path(file_path).name)
            
            result = {
                'test': '文档分类',
                'file': Path(file_path).name,
                'type': analysis.file_type.value,
                'strategy': analysis.processing_strategy,
                'pages': analysis.total_pages,
                'text_ratio': f"{analysis.text_page_ratio:.1%}",
                'scan_ratio': f"{analysis.scan_page_ratio:.1%}",
                'status': '✅ 通过' if expected_type is None or analysis.file_type == expected_type else '⚠️ 预期不符'
            }
            
            logger.info(f"  文件类型: {analysis.file_type.value}")
            logger.info(f"  处理策略: {analysis.processing_strategy}")
            logger.info(f"  总页数: {analysis.total_pages}")
            logger.info(f"  文本页比例: {analysis.text_page_ratio:.1%}")
            logger.info(f"  扫描页比例: {analysis.scan_page_ratio:.1%}")
            
            if analysis.is_financial_report:
                logger.info(f"  财务报告年份: {analysis.financial_years}")
                result['financial_years'] = analysis.financial_years
            
            if analysis.is_certificate:
                logger.info(f"  ✓ 检测为证件类型")
                result['is_certificate'] = True
            
            self.test_results.append(result)
            return analysis
            
        except Exception as e:
            logger.error(f"❌ 分类错误: {e}", exc_info=True)
            self.test_results.append({
                'test': '文档分类',
                'file': Path(file_path).name,
                'error': str(e),
                'status': '❌ 失败'
            })
            return None
    
    async def test_text_extraction(self, file_path: str):
        """测试文本提取"""
        logger.info(f"\n🔤 测试文本提取: {Path(file_path).name}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            # 测试直接文本提取
            extractor = DirectTextExtractor()
            text = extractor.extract(file_path)
            
            result = {
                'test': '文本提取',
                'file': Path(file_path).name,
                'text_length': len(text),
                'text_preview': text[:100] + '...' if len(text) > 100 else text,
                'status': '✅ 通过'
            }
            
            logger.info(f"  提取字数: {len(text)}")
            logger.info(f"  预览: {text[:100]}...")
            
            self.test_results.append(result)
            return text
            
        except Exception as e:
            logger.error(f"❌ 提取错误: {e}", exc_info=True)
            self.test_results.append({
                'test': '文本提取',
                'file': Path(file_path).name,
                'error': str(e),
                'status': '❌ 失败'
            })
            return None
    
    async def test_full_processing(self, file_path: str):
        """测试完整处理流程"""
        logger.info(f"\n⚙️  测试完整处理: {Path(file_path).name}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            result = await self.processor.process(file_path, Path(file_path).name)
            
            test_result = {
                'test': '完整处理',
                'file': Path(file_path).name,
                'status_code': result.get('status'),
                'file_type': result.get('file_type'),
                'strategy': result.get('processing_strategy'),
                'pages': result.get('total_pages'),
                'time': result.get('processing_time'),
            }
            
            logger.info(f"  状态: {result.get('status')}")
            logger.info(f"  文件类型: {result.get('file_type')}")
            logger.info(f"  处理策略: {result.get('processing_strategy')}")
            logger.info(f"  页数: {result.get('total_pages')}")
            
            if result.get('chapters'):
                logger.info(f"  提取章节数: {len(result['chapters'])}")
                test_result['chapters_count'] = len(result['chapters'])
                
                # 显示前 5 个章节
                for i, ch in enumerate(result['chapters'][:5]):
                    logger.info(f"    [{i+1}] {ch.get('title', 'N/A')} (L{ch.get('level')})")
            
            test_result['status'] = '✅ 通过'
            self.test_results.append(test_result)
            return result
            
        except Exception as e:
            logger.error(f"❌ 处理错误: {e}", exc_info=True)
            self.test_results.append({
                'test': '完整处理',
                'file': Path(file_path).name,
                'error': str(e),
                'status': '❌ 失败'
            })
            return None
    
    def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "="*60)
        logger.info("📊 测试报告汇总")
        logger.info("="*60)
        
        # 按测试类型分类
        tests_by_type = {}
        for result in self.test_results:
            test_type = result.get('test', '未知')
            if test_type not in tests_by_type:
                tests_by_type[test_type] = []
            tests_by_type[test_type].append(result)
        
        # 输出每类测试的汇总
        for test_type, results in tests_by_type.items():
            passed = sum(1 for r in results if '✅' in str(r.get('status', '')))
            total = len(results)
            logger.info(f"\n{test_type}: {passed}/{total} 通过")
            
            for result in results:
                status = result.get('status', '❌ 未知')
                file = result.get('file', 'N/A')
                logger.info(f"  {status} {file}")
                
                # 显示关键信息
                if result.get('type'):
                    logger.info(f"      类型: {result['type']}")
                if result.get('text_length'):
                    logger.info(f"      字数: {result['text_length']}")
                if result.get('chapters_count'):
                    logger.info(f"      章节: {result['chapters_count']}")
                if result.get('error'):
                    logger.info(f"      错误: {result['error']}")
        
        # 总计
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if '✅' in str(r.get('status', '')))
        logger.info(f"\n{'='*60}")
        logger.info(f"总计: {passed_tests}/{total_tests} 测试通过")
        logger.info(f"{'='*60}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'rate': f"{100 * passed_tests / total_tests:.1f}%" if total_tests > 0 else "0%",
            'results': self.test_results
        }


async def main():
    """主测试函数"""
    logger.info("🚀 开始文档处理系统测试\n")
    
    tester = DocumentProcessingTest()
    
    # 查找测试文件
    test_dir = Path(__file__).parent / 'uploads'
    test_files = []
    
    if test_dir.exists():
        # 查找所有 PDF 和 DOC 文件
        test_files.extend(list(test_dir.glob('*.pdf')))
        test_files.extend(list(test_dir.glob('*.docx')))
    
    if test_files:
        logger.info(f"📁 找到 {len(test_files)} 个测试文件\n")
        
        # 测试每个文件
        for file_path in test_files[:3]:  # 限制为前 3 个文件，避免耗时过长
            logger.info(f"\n{'='*60}")
            logger.info(f"测试文件: {file_path.name}")
            logger.info(f"{'='*60}")
            
            # 1. 测试分类
            analysis = await tester.test_classifier(str(file_path))
            
            # 2. 测试文本提取
            if analysis and analysis.file_type in [
                DocumentType.MAIN_PROPOSAL,
                DocumentType.UNKNOWN
            ]:
                await tester.test_text_extraction(str(file_path))
            
            # 3. 测试完整处理
            await tester.test_full_processing(str(file_path))
    else:
        logger.warning("⚠️  未找到测试文件。执行模拟测试...\n")
        
        # 执行模拟测试
        logger.info("📋 模拟测试 1: 文档分类器初始化")
        try:
            classifier = SmartDocumentClassifier()
            logger.info("  ✅ SmartDocumentClassifier 初始化成功")
        except Exception as e:
            logger.error(f"  ❌ 初始化失败: {e}")
        
        logger.info("\n🔤 模拟测试 2: OCR 提取器初始化")
        try:
            extractor = HybridTextExtractor(use_paddle_ocr=False)  # 禁用 OCR，只测试文本
            logger.info("  ✅ HybridTextExtractor 初始化成功")
        except Exception as e:
            logger.error(f"  ❌ 初始化失败: {e}")
        
        logger.info("\n⚙️  模拟测试 3: 文档处理器初始化")
        try:
            processor = DocumentProcessor()
            logger.info("  ✅ DocumentProcessor 初始化成功")
        except Exception as e:
            logger.error(f"  ❌ 初始化失败: {e}")
    
    # 生成报告
    report = tester.generate_report()
    
    # 保存报告
    report_path = Path(__file__).parent / 'TEST_REPORT.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"\n💾 报告已保存到: {report_path}")


if __name__ == '__main__':
    asyncio.run(main())
