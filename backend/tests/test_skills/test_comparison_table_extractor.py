"""
TableExtractor 新旧实现对比测试
验证新 Skill 与旧 PreprocessorAgent 实现的一致性

目的:
    确保从 PreprocessorAgent 迁移到 TableExtractor Skill 后，
    表格提取的结果保持一致，不会破坏现有功能。

策略:
    1. 使用相同的输入数据
    2. 对比输出结构和内容
    3. 验证 Markdown 格式一致性
"""

import pytest
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from unittest.mock import Mock, patch

# 配置 pytest-asyncio
pytestmark = pytest.mark.asyncio

# 旧实现 (PreprocessorAgent)
from agents.preprocessor import PreprocessorAgent, TableBlock

# 新实现 (TableExtractor Skill)
from skills.table_extractor import (
    TableExtractor,
    TableExtractorInput,
    TableData
)


# ========== Fixtures ==========

@pytest.fixture
def old_agent():
    """创建旧实现（PreprocessorAgent）实例"""
    return PreprocessorAgent()


@pytest.fixture
def new_skill():
    """创建新实现（TableExtractor）实例"""
    return TableExtractor()


@pytest.fixture
def mock_page_with_simple_table():
    """模拟包含简单表格的页面"""
    page = Mock()
    page.extract_tables = Mock(return_value=[
        [
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"]
        ]
    ])
    return page


@pytest.fixture
def mock_page_with_complex_table():
    """模拟包含复杂表格的页面"""
    page = Mock()
    page.extract_tables = Mock(return_value=[
        [
            ["Product", "Price", "Stock", "Status"],
            ["Apple", "$1.99", "100", "Available"],
            ["Orange", "$2.49", "50", "Available"],
            ["Banana", None, "75", "Out of Stock"]
        ],
        [
            ["Header1", "Header2"],
            ["Data1", "Data2"]
        ]
    ])
    return page


@pytest.fixture
def mock_page_empty():
    """模拟空页面（无表格）"""
    page = Mock()
    page.extract_tables = Mock(return_value=[])
    return page


# ========== 辅助函数 ==========

def normalize_table_block(old_block: TableBlock) -> Dict[str, Any]:
    """
    将旧实现的 TableBlock 转换为标准格式
    
    Args:
        old_block: PreprocessorAgent 的 TableBlock
    
    Returns:
        Dict: 标准化后的字典
    """
    return {
        "table_id": old_block.table_id,
        "page_number": old_block.page_number,
        "markdown_content": old_block.markdown_content,
        "row_count": old_block.row_count,
        "col_count": old_block.col_count,
        "headers": old_block.headers,
        "data": old_block.data
    }


def normalize_table_data(new_data: TableData) -> Dict[str, Any]:
    """
    将新实现的 TableData 转换为标准格式
    
    Args:
        new_data: TableExtractor 的 TableData
    
    Returns:
        Dict: 标准化后的字典
    """
    return new_data.model_dump()


def compare_table_structures(old_tables: List[TableBlock], new_tables: List[TableData]) -> bool:
    """
    对比两个表格列表的结构
    
    Args:
        old_tables: 旧实现的表格列表
        new_tables: 新实现的表格列表
    
    Returns:
        bool: 结构是否一致
    """
    if len(old_tables) != len(new_tables):
        return False
    
    for old, new in zip(old_tables, new_tables):
        old_norm = normalize_table_block(old)
        new_norm = normalize_table_data(new)
        
        # 对比关键字段
        if old_norm["page_number"] != new_norm["page_number"]:
            return False
        if old_norm["row_count"] != new_norm["row_count"]:
            return False
        if old_norm["col_count"] != new_norm["col_count"]:
            return False
        if len(old_norm["headers"]) != len(new_norm["headers"]):
            return False
        if len(old_norm["data"]) != len(new_norm["data"]):
            return False
    
    return True


def compare_markdown_content(old_markdown: str, new_markdown: str) -> bool:
    """
    对比 Markdown 内容（忽略空白差异）
    
    Args:
        old_markdown: 旧实现的 Markdown
        new_markdown: 新实现的 Markdown
    
    Returns:
        bool: 内容是否一致
    """
    # 移除首尾空白并按行分割
    old_lines = [line.strip() for line in old_markdown.strip().split('\n')]
    new_lines = [line.strip() for line in new_markdown.strip().split('\n')]
    
    return old_lines == new_lines


# ========== 对比测试 ==========

class TestTableExtractionComparison:
    """对比新旧实现的表格提取功能"""
    
    async def test_simple_table_extraction_consistency(
        self, 
        old_agent, 
        new_skill, 
        mock_page_with_simple_table
    ):
        """测试简单表格提取的一致性"""
        page_num = 1
        
        # 旧实现提取
        old_tables = await old_agent._extract_tables(mock_page_with_simple_table, page_num)
        
        # 新实现提取
        new_tables = new_skill._extract_tables_from_page(
            mock_page_with_simple_table, 
            page_num, 
            {}
        )
        
        # 验证表格数量一致
        assert len(old_tables) == len(new_tables) == 1
        
        # 验证结构一致
        assert compare_table_structures(old_tables, new_tables)
        
        # 验证具体内容
        old_table = old_tables[0]
        new_table = new_tables[0]
        
        assert old_table.page_number == new_table.page_number == 1
        assert old_table.row_count == new_table.row_count == 3
        assert old_table.col_count == new_table.col_count == 3
        assert old_table.headers == new_table.headers == ["Name", "Age", "City"]
    
    async def test_complex_table_extraction_consistency(
        self,
        old_agent,
        new_skill,
        mock_page_with_complex_table
    ):
        """测试复杂表格（多表格、None值）的一致性"""
        page_num = 2
        
        # 旧实现提取
        old_tables = await old_agent._extract_tables(mock_page_with_complex_table, page_num)
        
        # 新实现提取
        new_tables = new_skill._extract_tables_from_page(
            mock_page_with_complex_table,
            page_num,
            {}
        )
        
        # 验证表格数量一致（应该有2个表格）
        assert len(old_tables) == len(new_tables) == 2
        
        # 验证结构一致
        assert compare_table_structures(old_tables, new_tables)
        
        # 验证第一个表格（包含 None 值）
        old_table1 = old_tables[0]
        new_table1 = new_tables[0]
        
        assert old_table1.row_count == new_table1.row_count == 4
        assert old_table1.col_count == new_table1.col_count == 4
        
        # 验证 None 值处理一致（应该转为空字符串）
        old_data_row2 = old_table1.data[2]  # Banana 行
        new_data_row2 = new_table1.data[2]
        
        # 两者都应该将 None 转为空字符串
        assert old_data_row2[1] == new_data_row2[1] == ""
    
    async def test_empty_page_consistency(
        self,
        old_agent,
        new_skill,
        mock_page_empty
    ):
        """测试空页面（无表格）的一致性"""
        page_num = 3
        
        # 旧实现提取
        old_tables = await old_agent._extract_tables(mock_page_empty, page_num)
        
        # 新实现提取
        new_tables = new_skill._extract_tables_from_page(
            mock_page_empty,
            page_num,
            {}
        )
        
        # 两者都应该返回空列表
        assert len(old_tables) == len(new_tables) == 0


class TestMarkdownConversionComparison:
    """对比新旧实现的 Markdown 转换功能"""
    
    def test_markdown_conversion_consistency_basic(self, old_agent, new_skill):
        """测试基本 Markdown 转换的一致性"""
        headers = ["Name", "Age", "City"]
        data = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"]
        ]
        
        # 旧实现转换
        old_markdown = old_agent._table_to_markdown(headers, data)
        
        # 新实现转换
        new_markdown = new_skill._table_to_markdown(headers, data)
        
        # 验证 Markdown 内容一致
        assert compare_markdown_content(old_markdown, new_markdown)
        
        # 验证包含关键元素
        assert "| Name | Age | City |" in old_markdown
        assert "| Name | Age | City |" in new_markdown
        assert "| Alice | 30 | NYC |" in old_markdown
        assert "| Alice | 30 | NYC |" in new_markdown
    
    def test_markdown_conversion_with_none_values(self, old_agent, new_skill):
        """测试包含 None 值的 Markdown 转换一致性"""
        # 注意：在实际使用中，headers 会先被 str() 转换
        # 所以这里模拟实际场景：headers 已经是字符串
        headers = ["Col1", "None", "Col3"]  # None 已经转为 "None"
        data = [
            ["A", None, "C"],
            [None, "B", None]
        ]
        
        # 旧实现转换
        old_markdown = old_agent._table_to_markdown(headers, data)
        
        # 新实现转换
        new_markdown = new_skill._table_to_markdown(headers, data)
        
        # 验证 Markdown 内容一致
        assert compare_markdown_content(old_markdown, new_markdown)
        
        # 验证 None 值处理一致（data 中的 None 转为空字符串）
        assert "|  |" in old_markdown  # 空单元格
        assert "|  |" in new_markdown
    
    def test_markdown_conversion_with_unequal_columns(self, old_agent, new_skill):
        """测试列数不匹配的 Markdown 转换一致性"""
        headers = ["A", "B", "C"]
        data = [
            ["1", "2"],  # 缺少一列
            ["3", "4", "5", "6"]  # 多一列
        ]
        
        # 旧实现转换
        old_markdown = old_agent._table_to_markdown(headers, data)
        
        # 新实现转换
        new_markdown = new_skill._table_to_markdown(headers, data)
        
        # 验证 Markdown 内容一致
        assert compare_markdown_content(old_markdown, new_markdown)
        
        # 验证都正确处理了列数不匹配
        # 缺失的列应该补空，多余的列应该截断
        lines_old = old_markdown.split('\n')
        lines_new = new_markdown.split('\n')
        
        # 每行都应该有3个数据列（匹配表头）
        for line in lines_old[2:]:  # 跳过表头和分隔符
            if line.strip():
                assert line.count('|') == 4  # 3列 + 2个边界 = 4个分隔符
        
        for line in lines_new[2:]:
            if line.strip():
                assert line.count('|') == 4


class TestEndToEndComparison:
    """端到端对比测试"""
    
    @patch('skills.table_extractor.pdfplumber.open')
    async def test_full_document_extraction_comparison(
        self,
        mock_open,
        old_agent,
        new_skill,
        tmp_path
    ):
        """测试完整文档提取的一致性"""
        # 创建临时 PDF 文件
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        # 模拟 PDF 内容（2页，每页1个表格）
        mock_pdf = Mock()
        
        page1 = Mock()
        page1.extract_tables = Mock(return_value=[
            [["Name", "Score"], ["Alice", "95"], ["Bob", "87"]]
        ])
        
        page2 = Mock()
        page2.extract_tables = Mock(return_value=[
            [["Item", "Qty"], ["Apple", "10"], ["Orange", "5"]]
        ])
        
        mock_pdf.pages = [page1, page2]
        
        mock_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        # 旧实现：逐页提取
        old_all_tables = []
        for idx, page in enumerate(mock_pdf.pages):
            page_tables = await old_agent._extract_tables(page, idx + 1)
            old_all_tables.extend(page_tables)
        
        # 新实现：使用 execute 方法
        input_data = TableExtractorInput(file_path=str(pdf_file))
        output = new_skill.execute(input_data)
        new_all_tables = output.tables
        
        # 验证表格总数一致
        assert len(old_all_tables) == len(new_all_tables) == 2
        
        # 验证每个表格的内容一致
        for old_table, new_table in zip(old_all_tables, new_all_tables):
            old_norm = normalize_table_block(old_table)
            new_norm = normalize_table_data(new_table)
            
            # 验证基本属性
            assert old_norm["page_number"] == new_norm["page_number"]
            assert old_norm["row_count"] == new_norm["row_count"]
            assert old_norm["col_count"] == new_norm["col_count"]
            assert old_norm["headers"] == new_norm["headers"]
            assert old_norm["data"] == new_norm["data"]
            
            # 验证 Markdown 内容一致
            assert compare_markdown_content(
                old_norm["markdown_content"],
                new_norm["markdown_content"]
            )


class TestPerformanceComparison:
    """性能对比测试（可选）"""
    
    async def test_extraction_speed_similar(
        self,
        old_agent,
        new_skill,
        mock_page_with_simple_table
    ):
        """测试提取速度相近（新实现不应明显变慢）"""
        import time
        
        page_num = 1
        iterations = 100
        
        # 测试旧实现性能
        start_old = time.time()
        for _ in range(iterations):
            await old_agent._extract_tables(mock_page_with_simple_table, page_num)
        time_old = time.time() - start_old
        
        # 测试新实现性能
        start_new = time.time()
        for _ in range(iterations):
            new_skill._extract_tables_from_page(
                mock_page_with_simple_table,
                page_num,
                {}
            )
        time_new = time.time() - start_new
        
        # 新实现性能不应下降超过 100%（允许翻倍，因为是独立实现）
        # 主要验证不会慢10倍以上
        assert time_new <= time_old * 10, \
            f"新实现过慢: {time_new:.4f}s vs {time_old:.4f}s"
        
        # 记录性能数据供参考
        print(f"\n性能对比: 旧实现 {time_old:.4f}s, 新实现 {time_new:.4f}s, 比率 {time_new/time_old:.2f}x")


# ========== 数据一致性验证 ==========

class TestDataConsistency:
    """验证数据处理的一致性"""
    
    async def test_table_id_format_consistency(
        self,
        old_agent,
        new_skill,
        mock_page_with_simple_table
    ):
        """测试 table_id 格式一致性"""
        page_num = 5
        
        old_tables = await old_agent._extract_tables(mock_page_with_simple_table, page_num)
        new_tables = new_skill._extract_tables_from_page(
            mock_page_with_simple_table,
            page_num,
            {}
        )
        
        # 验证 table_id 格式一致：page{page_num}_table{idx}
        assert old_tables[0].table_id == "page5_table0"
        assert new_tables[0].table_id == "page5_table0"
    
    async def test_headers_extraction_consistency(
        self,
        old_agent,
        new_skill
    ):
        """测试表头提取的一致性"""
        page = Mock()
        page.extract_tables = Mock(return_value=[
            [
                [123, None, "Text"],  # 混合类型的表头
                ["A", "B", "C"]
            ]
        ])
        
        old_tables = await old_agent._extract_tables(page, 1)
        new_tables = new_skill._extract_tables_from_page(page, 1, {})
        
        # 验证表头都转为字符串，None转为字符串"None"（与旧实现一致）
        assert old_tables[0].headers == ["123", "None", "Text"]
        assert new_tables[0].headers == ["123", "None", "Text"]


# ========== 运行测试 ==========

if __name__ == "__main__":
    """
    运行对比测试
    
    命令:
        docker compose exec backend sh -c "cd /app && PYTHONPATH=/app python3 -m pytest tests/test_skills/test_comparison_table_extractor.py -v"
    """
    pytest.main([__file__, "-v", "--tb=short"])
