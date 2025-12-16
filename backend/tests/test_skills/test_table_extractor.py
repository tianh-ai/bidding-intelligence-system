"""
TableExtractor Skill 单元测试
测试覆盖率目标: > 80%

测试策略:
1. 基础功能: 初始化、元数据、验证
2. 核心功能: 表格提取、Markdown 转换
3. 边界条件: 空文件、无表格、特殊字符
4. 错误处理: 文件不存在、格式错误
"""

import pytest
from pathlib import Path
from pydantic import ValidationError
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from skills.table_extractor import (
    TableExtractor,
    TableExtractorInput,
    TableExtractorOutput,
    TableData
)


# ========== Fixtures ==========

@pytest.fixture
def extractor():
    """创建 TableExtractor 实例"""
    return TableExtractor(config={"debug": True})


@pytest.fixture
def valid_input(tmp_path):
    """创建有效的输入数据（使用临时文件）"""
    # 创建临时 PDF 文件
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")  # 最小化的 PDF 文件头
    
    return TableExtractorInput(
        file_path=str(pdf_file),
        page_numbers=None,
        extract_options={}
    )


@pytest.fixture
def mock_pdfplumber_page():
    """模拟 pdfplumber.Page 对象"""
    page = Mock()
    
    # 模拟提取的表格数据
    mock_table = [
        ["Header1", "Header2", "Header3"],
        ["Cell1", "Cell2", "Cell3"],
        ["Cell4", "Cell5", "Cell6"]
    ]
    
    page.extract_tables = Mock(return_value=[mock_table])
    return page


@pytest.fixture
def mock_pdf_with_tables():
    """模拟包含表格的 PDF"""
    pdf = Mock()
    
    # 创建两页，每页有表格
    page1 = Mock()
    page1.extract_tables = Mock(return_value=[
        [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
    ])
    
    page2 = Mock()
    page2.extract_tables = Mock(return_value=[
        [["Product", "Price"], ["Apple", "$1"], ["Orange", "$2"]]
    ])
    
    pdf.pages = [page1, page2]
    return pdf


# ========== 基础功能测试 ==========

class TestTableExtractorBasic:
    """测试 TableExtractor 基础功能"""
    
    def test_initialization(self):
        """测试 Skill 初始化"""
        extractor = TableExtractor()
        assert extractor is not None
        assert extractor.config == {}
        assert extractor.default_extract_options == {}
    
    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        config = {
            "debug": True,
            "default_extract_options": {"vertical_strategy": "lines"}
        }
        extractor = TableExtractor(config=config)
        assert extractor.config == config
        assert extractor.default_extract_options == {"vertical_strategy": "lines"}
    
    def test_get_metadata(self, extractor):
        """测试获取元数据"""
        metadata = extractor.get_metadata()
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert "source" in metadata
        assert metadata["name"] == "TableExtractor"
        assert metadata["version"] == "1.0.0"
        assert "pdfplumber" in metadata["dependencies"]


# ========== 输入验证测试 ==========

class TestTableExtractorValidation:
    """测试输入验证功能"""
    
    def test_validate_valid_input(self, extractor, valid_input):
        """测试验证有效输入"""
        assert extractor.validate(valid_input) == True
    
    def test_validate_empty_path(self, extractor):
        """测试验证空路径"""
        input_data = TableExtractorInput(file_path="")
        assert extractor.validate(input_data) == False
    
    def test_validate_non_pdf_file(self, extractor):
        """测试验证非 PDF 文件"""
        input_data = TableExtractorInput(file_path="document.docx")
        assert extractor.validate(input_data) == False
    
    def test_validate_invalid_page_numbers(self, extractor):
        """测试验证无效页码"""
        input_data = TableExtractorInput(
            file_path="test.pdf",
            page_numbers=[0, -1]  # 页码必须 >= 1
        )
        assert extractor.validate(input_data) == False
    
    def test_pydantic_validation_error(self):
        """测试 Pydantic 类型验证"""
        with pytest.raises(ValidationError):
            # file_path 是必填字段
            TableExtractorInput(page_numbers=[1, 2])


# ========== Markdown 转换测试 ==========

class TestMarkdownConversion:
    """测试表格转 Markdown 功能"""
    
    def test_table_to_markdown_basic(self, extractor):
        """测试基本的 Markdown 转换"""
        headers = ["Name", "Age", "City"]
        data = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"]
        ]
        
        markdown = extractor._table_to_markdown(headers, data)
        
        assert "| Name | Age | City |" in markdown
        assert "| --- | --- | --- |" in markdown
        assert "| Alice | 30 | NYC |" in markdown
        assert "| Bob | 25 | LA |" in markdown
    
    def test_table_to_markdown_empty_headers(self, extractor):
        """测试空表头"""
        markdown = extractor._table_to_markdown([], [])
        assert markdown == ""
    
    def test_table_to_markdown_with_none_values(self, extractor):
        """测试包含 None 值的表格（headers: None→"None", data: None→""）"""
        headers = ["Name", None, "City"]
        data = [
            ["Alice", None, "NYC"],
            [None, "25", None]
        ]
        
        markdown = extractor._table_to_markdown(headers, data)
        
        # headers 中的 None → "None"，data 中的 None → 空字符串
        assert "| Name | None | City |" in markdown
        assert "| Alice |  | NYC |" in markdown
        assert "|  | 25 |  |" in markdown
    
    def test_table_to_markdown_unequal_columns(self, extractor):
        """测试列数不匹配（自动补齐）"""
        headers = ["Name", "Age", "City"]
        data = [
            ["Alice", "30"],  # 缺少一列
            ["Bob", "25", "LA", "Extra"]  # 多一列
        ]
        
        markdown = extractor._table_to_markdown(headers, data)
        
        # 缺失的列应该补空
        assert "| Alice | 30 |  |" in markdown
        # 多余的列应该截断
        assert "| Bob | 25 | LA |" in markdown
        assert "Extra" not in markdown
    
    def test_table_to_markdown_special_characters(self, extractor):
        """测试特殊字符"""
        headers = ["Name", "Price"]
        data = [
            ["Apple", "$1.99"],
            ["Orange | Banana", "€2.50"],
            ["测试中文", "¥10"]
        ]
        
        markdown = extractor._table_to_markdown(headers, data)
        
        assert "Apple" in markdown
        assert "$1.99" in markdown
        assert "€2.50" in markdown
        assert "测试中文" in markdown


# ========== 表格提取测试 ==========

class TestTableExtraction:
    """测试表格提取功能"""
    
    def test_extract_tables_from_page(self, extractor, mock_pdfplumber_page):
        """测试从单页提取表格"""
        tables = extractor._extract_tables_from_page(
            mock_pdfplumber_page,
            page_num=1,
            extract_options={}
        )
        
        assert len(tables) == 1
        assert tables[0].table_id == "page1_table0"
        assert tables[0].page_number == 1
        assert tables[0].row_count == 3
        assert tables[0].col_count == 3
        assert tables[0].headers == ["Header1", "Header2", "Header3"]
    
    def test_extract_tables_from_page_empty(self, extractor):
        """测试提取空页面（无表格）"""
        page = Mock()
        page.extract_tables = Mock(return_value=[])
        
        tables = extractor._extract_tables_from_page(page, 1, {})
        assert len(tables) == 0
    
    def test_extract_tables_from_page_with_options(self, extractor):
        """测试使用自定义选项提取"""
        page = Mock()
        page.extract_tables = Mock(return_value=[
            [["A", "B"], ["1", "2"]]
        ])
        
        options = {"vertical_strategy": "lines"}
        tables = extractor._extract_tables_from_page(page, 1, options)
        
        # 验证调用时传递了选项
        page.extract_tables.assert_called_once()
        assert len(tables) == 1
    
    def test_extract_tables_handles_pdfplumber_error(self, extractor):
        """测试处理 pdfplumber 提取错误"""
        page = Mock()
        page.extract_tables = Mock(side_effect=Exception("pdfplumber error"))
        
        # 应该捕获异常并返回空列表
        tables = extractor._extract_tables_from_page(page, 1, {})
        assert len(tables) == 0


# ========== 完整执行测试 ==========

class TestTableExtractorExecution:
    """测试完整的执行流程"""
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_execute_success(self, mock_open, extractor, tmp_path):
        """测试成功执行"""
        # 创建临时 PDF 文件
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        # 模拟 pdfplumber
        mock_pdf = Mock()
        mock_pdf.pages = [Mock()]
        mock_pdf.pages[0].extract_tables = Mock(return_value=[
            [["Name", "Age"], ["Alice", "30"]]
        ])
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        input_data = TableExtractorInput(file_path=str(pdf_file))
        output = extractor.execute(input_data)
        
        assert isinstance(output, TableExtractorOutput)
        assert output.file_path == str(pdf_file)
        assert output.total_pages == 1
        assert output.table_count == 1
        assert len(output.tables) == 1
        assert "extraction_time_ms" in output.metadata
    
    def test_execute_file_not_found(self, extractor):
        """测试文件不存在的情况"""
        input_data = TableExtractorInput(file_path="/nonexistent/file.pdf")
        
        with pytest.raises(FileNotFoundError):
            extractor.execute(input_data)
    
    def test_execute_validation_failure(self, extractor):
        """测试输入验证失败"""
        input_data = TableExtractorInput(file_path="")
        
        with pytest.raises(ValueError, match="输入数据验证失败"):
            extractor.execute(input_data)
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_execute_with_specific_pages(self, mock_open, extractor, tmp_path):
        """测试提取指定页码"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        # 模拟 3 页 PDF
        mock_pdf = Mock()
        mock_pdf.pages = [Mock(), Mock(), Mock()]
        for page in mock_pdf.pages:
            page.extract_tables = Mock(return_value=[])
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        # 只提取第 1 和 3 页
        input_data = TableExtractorInput(
            file_path=str(pdf_file),
            page_numbers=[1, 3]
        )
        output = extractor.execute(input_data)
        
        assert output.total_pages == 3
        assert output.processed_pages == [1, 3]
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_execute_with_invalid_page_range(self, mock_open, extractor, tmp_path):
        """测试页码超出范围（自动过滤）"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        mock_pdf = Mock()
        mock_pdf.pages = [Mock(), Mock()]  # 只有 2 页
        for page in mock_pdf.pages:
            page.extract_tables = Mock(return_value=[])
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        # 请求第 1-5 页（只有 1-2 存在）
        input_data = TableExtractorInput(
            file_path=str(pdf_file),
            page_numbers=[1, 2, 3, 4, 5]
        )
        output = extractor.execute(input_data)
        
        # 只处理存在的页
        assert output.processed_pages == [1, 2]
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_execute_handles_page_extraction_error(self, mock_open, extractor, tmp_path):
        """测试处理单页提取错误"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        mock_pdf = Mock()
        page1 = Mock()
        page1.extract_tables = Mock(return_value=[[["A", "B"]]])
        
        page2 = Mock()
        page2.extract_tables = Mock(side_effect=Exception("Page error"))
        
        mock_pdf.pages = [page1, page2]
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        input_data = TableExtractorInput(file_path=str(pdf_file))
        output = extractor.execute(input_data)
        
        # 两页都会被"处理"，但第二页提取失败返回空列表
        # _extract_tables_from_page 内部捕获异常，不会向上传播
        assert output.total_pages == 2
        assert len(output.processed_pages) == 2  # 两页都被处理
        assert output.table_count == 1  # 只有第一页成功提取表格
        # error_pages 为空，因为异常在 _extract_tables_from_page 内被捕获


# ========== 边界条件测试 ==========

class TestTableExtractorEdgeCases:
    """测试边界条件"""
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_execute_empty_pdf(self, mock_open, extractor, tmp_path):
        """测试空 PDF（0 页）"""
        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        mock_pdf = Mock()
        mock_pdf.pages = []
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        input_data = TableExtractorInput(file_path=str(pdf_file))
        output = extractor.execute(input_data)
        
        assert output.total_pages == 0
        assert output.table_count == 0
        assert len(output.tables) == 0
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_execute_pdf_without_tables(self, mock_open, extractor, tmp_path):
        """测试无表格的 PDF"""
        pdf_file = tmp_path / "no_tables.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        mock_pdf = Mock()
        mock_pdf.pages = [Mock()]
        mock_pdf.pages[0].extract_tables = Mock(return_value=[])
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        input_data = TableExtractorInput(file_path=str(pdf_file))
        output = extractor.execute(input_data)
        
        assert output.total_pages == 1
        assert output.table_count == 0
    
    def test_table_data_model_validation(self):
        """测试 TableData 模型验证"""
        # 有效数据
        table = TableData(
            table_id="test_table",
            page_number=1,
            markdown_content="| A | B |\n|---|---|",
            row_count=2,
            col_count=2,
            headers=["A", "B"],
            data=[["1", "2"]]
        )
        assert table.table_id == "test_table"
        
        # 缺少必填字段
        with pytest.raises(ValidationError):
            TableData(page_number=1)


# ========== 集成测试 ==========

class TestTableExtractorIntegration:
    """集成测试（与实际组件交互）"""
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_output_serialization(self, mock_open, extractor, tmp_path):
        """测试输出序列化"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        mock_pdf = Mock()
        mock_pdf.pages = [Mock()]
        mock_pdf.pages[0].extract_tables = Mock(return_value=[
            [["Name", "Age"], ["Alice", "30"]]
        ])
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        input_data = TableExtractorInput(file_path=str(pdf_file))
        output = extractor.execute(input_data)
        
        # 测试输出可以序列化为 JSON
        output_dict = output.model_dump()
        assert isinstance(output_dict, dict)
        assert "file_path" in output_dict
        assert "tables" in output_dict
        
        # 测试表格数据也可以序列化
        if output.tables:
            table_dict = output.tables[0].model_dump()
            assert isinstance(table_dict, dict)
    
    @patch('skills.table_extractor.pdfplumber.open')
    def test_markdown_output_quality(self, mock_open, extractor, tmp_path):
        """测试 Markdown 输出质量"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        mock_pdf = Mock()
        mock_pdf.pages = [Mock()]
        mock_pdf.pages[0].extract_tables = Mock(return_value=[
            [["Product", "Price", "Stock"], 
             ["Apple", "$1.99", "100"],
             ["Orange", "$2.49", "50"]]
        ])
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        input_data = TableExtractorInput(file_path=str(pdf_file))
        output = extractor.execute(input_data)
        
        assert len(output.tables) == 1
        markdown = output.tables[0].markdown_content
        
        # 验证 Markdown 格式正确
        lines = markdown.split("\n")
        assert len(lines) == 4  # 表头 + 分隔符 + 2 行数据
        assert lines[0].startswith("| Product")
        assert "---" in lines[1]
        assert "Apple" in lines[2]
        assert "Orange" in lines[3]


# ========== 运行测试 ==========

if __name__ == "__main__":
    """
    直接运行此文件进行测试
    
    命令:
        python -m pytest backend/tests/test_skills/test_table_extractor.py -v
        python -m pytest backend/tests/test_skills/test_table_extractor.py -v --cov=skills.table_extractor --cov-report=html
    """
    pytest.main([__file__, "-v", "--tb=short"])
