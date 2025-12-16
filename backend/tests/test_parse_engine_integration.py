#!/usr/bin/env python3
"""
Phase 2.5 验证测试：TableExtractor 集成到 ParseEngine
验证无回归，表格提取功能正常
"""

import pytest
import os
from pathlib import Path

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "test_data"


class TestParseEngineIntegration:
    """验证 ParseEngine 集成 TableExtractor 后功能正常"""
    
    def test_parse_engine_initialization_with_tables(self):
        """测试初始化 ParseEngine（启用表格提取）"""
        from engines.parse_engine import ParseEngine
        
        engine = ParseEngine(use_table_skill=True)
        assert engine.use_table_skill is True
        assert engine._table_extractor is None  # 懒加载未触发
    
    def test_parse_engine_initialization_without_tables(self):
        """测试初始化 ParseEngine（禁用表格提取）"""
        from engines.parse_engine import ParseEngine
        
        engine = ParseEngine(use_table_skill=False)
        assert engine.use_table_skill is False
        assert engine._table_extractor is None
    
    def test_table_extractor_lazy_loading(self):
        """测试 TableExtractor 懒加载"""
        from engines.parse_engine import ParseEngine
        
        engine = ParseEngine(use_table_skill=True)
        assert engine._table_extractor is None
        
        # 触发懒加载
        extractor = engine.table_extractor
        assert extractor is not None
        assert engine._table_extractor is extractor  # 同一实例
    
    def test_table_extractor_disabled_no_loading(self):
        """测试禁用表格提取时不加载 TableExtractor"""
        from engines.parse_engine import ParseEngine
        
        engine = ParseEngine(use_table_skill=False)
        extractor = engine.table_extractor
        assert extractor is None  # 不应该加载
    
    def test_extract_tables_method_exists(self):
        """测试 _extract_tables_from_pdf 方法存在"""
        from engines.parse_engine import ParseEngine
        
        engine = ParseEngine(use_table_skill=True)
        assert hasattr(engine, '_extract_tables_from_pdf')
        assert callable(engine._extract_tables_from_pdf)
    
    def test_extract_tables_from_sample_pdf(self):
        """测试从样本 PDF 提取表格"""
        from engines.parse_engine import ParseEngine
        
        # 使用项目中已有的测试PDF
        test_pdf = TEST_DATA_DIR / "sample_table.pdf"
        if not test_pdf.exists():
            pytest.skip(f"测试文件不存在: {test_pdf}")
        
        engine = ParseEngine(use_table_skill=True)
        tables = engine._extract_tables_from_pdf(str(test_pdf))
        
        # 基本验证
        assert isinstance(tables, list)
        # 如果PDF包含表格，验证格式
        if tables:
            for table in tables:
                assert 'page_number' in table
                assert 'markdown' in table
                assert 'headers' in table
                assert 'data' in table
                assert 'table_id' in table
    
    def test_extract_tables_disabled_returns_empty(self):
        """测试禁用表格提取时返回空列表"""
        from engines.parse_engine import ParseEngine
        
        test_pdf = TEST_DATA_DIR / "sample_table.pdf"
        if not test_pdf.exists():
            pytest.skip(f"测试文件不存在: {test_pdf}")
        
        engine = ParseEngine(use_table_skill=False)
        tables = engine._extract_tables_from_pdf(str(test_pdf))
        
        # 禁用时应返回空列表
        assert tables == []
    
    def test_extract_tables_nonexistent_file(self):
        """测试提取不存在的文件"""
        from engines.parse_engine import ParseEngine
        
        engine = ParseEngine(use_table_skill=True)
        tables = engine._extract_tables_from_pdf("/nonexistent/file.pdf")
        
        # 错误应被捕获，返回空列表
        assert tables == []
    
    def test_parse_result_contains_tables(self):
        """测试 parse() 返回结果包含表格字段"""
        from engines.parse_engine import ParseEngine
        
        # 使用项目中已有的测试PDF
        test_pdf = TEST_DATA_DIR / "sample_table.pdf"
        if not test_pdf.exists():
            pytest.skip(f"测试文件不存在: {test_pdf}")
        
        engine = ParseEngine(use_table_skill=True)
        result = engine.parse(str(test_pdf), doc_type="reference", save_to_db=False)
        
        # 验证返回结构
        assert 'tables' in result
        assert 'table_count' in result
        assert isinstance(result['tables'], list)
        assert isinstance(result['table_count'], int)
        assert result['table_count'] == len(result['tables'])
    
    def test_backward_compatibility_images_still_work(self):
        """测试向后兼容：图片提取仍然正常"""
        from engines.parse_engine import ParseEngine
        
        test_pdf = TEST_DATA_DIR / "sample_table.pdf"
        if not test_pdf.exists():
            pytest.skip(f"测试文件不存在: {test_pdf}")
        
        engine = ParseEngine(use_table_skill=True)
        result = engine.parse(str(test_pdf), doc_type="reference", save_to_db=False)
        
        # 验证图片字段仍存在（向后兼容）
        assert 'images' in result
        assert 'image_count' in result


class TestParseEngineRegression:
    """回归测试：确保现有功能未受影响"""
    
    def test_parse_pdf_basic_functionality(self):
        """测试基本 PDF 解析功能未受影响"""
        from engines.parse_engine import ParseEngine
        
        test_pdf = TEST_DATA_DIR / "sample_table.pdf"
        if not test_pdf.exists():
            pytest.skip(f"测试文件不存在: {test_pdf}")
        
        engine = ParseEngine(use_table_skill=True)
        result = engine.parse(str(test_pdf), doc_type="reference", save_to_db=False)
        
        # 验证基础字段仍存在
        assert 'file_id' in result
        assert 'filename' in result
        assert 'content' in result
        assert 'total_chapters' in result
        assert 'chapters' in result
    
    def test_parse_docx_unaffected(self):
        """测试 DOCX 解析未受影响（不提取表格）"""
        from engines.parse_engine import ParseEngine
        
        # DOCX 文件不应触发表格提取
        engine = ParseEngine(use_table_skill=True)
        
        # 创建临时 DOCX（如果不存在）
        test_docx = TEST_DATA_DIR / "sample.docx"
        if not test_docx.exists():
            pytest.skip(f"测试文件不存在: {test_docx}")
        
        result = engine.parse(str(test_docx), doc_type="reference", save_to_db=False)
        
        # DOCX 应该不提取表格（当前实现）
        assert result['table_count'] == 0
        assert result['tables'] == []


class TestSkillMetadata:
    """验证 Skill 元数据"""
    
    def test_table_extractor_metadata(self):
        """验证 TableExtractor Skill 元数据正确"""
        from engines.parse_engine import ParseEngine
        
        engine = ParseEngine(use_table_skill=True)
        extractor = engine.table_extractor
        
        metadata = extractor.get_metadata()
        
        assert metadata['name'] == 'TableExtractor'
        assert metadata['version'] == '1.0.0'
        assert 'description' in metadata
        assert 'dependencies' in metadata
        assert 'pdfplumber' in metadata['dependencies']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
