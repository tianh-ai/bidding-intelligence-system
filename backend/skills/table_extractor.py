"""
TableExtractor Skill
从 PDF 文档中提取表格并转换为 Markdown 格式

迁移自: agents/preprocessor.py 中的表格提取逻辑
职责: 使用 pdfplumber 提取表格并格式化输出
特点: 独立、可测试、可复用
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import pdfplumber

from core.logger import logger


# ========== 输入输出模型 ==========

class TableExtractorInput(BaseModel):
    """
    TableExtractor 输入参数
    
    支持两种模式:
    1. 提取整个 PDF 文件的所有表格
    2. 提取指定页面的表格
    """
    file_path: str = Field(..., description="PDF 文件路径")
    page_numbers: Optional[List[int]] = Field(
        None, 
        description="指定要提取的页码列表 (从1开始)，None表示提取所有页"
    )
    extract_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="pdfplumber 提取选项，如 {'vertical_strategy': 'lines'}"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/path/to/document.pdf",
                "page_numbers": [1, 2, 3],
                "extract_options": {}
            }
        }


class TableData(BaseModel):
    """单个表格数据"""
    table_id: str = Field(..., description="表格唯一标识: page{页码}_table{索引}")
    page_number: int = Field(..., description="表格所在页码")
    markdown_content: str = Field(..., description="Markdown 格式的表格")
    row_count: int = Field(..., description="行数（包括表头）")
    col_count: int = Field(..., description="列数")
    headers: List[str] = Field(default_factory=list, description="表头列表")
    data: List[List[str]] = Field(default_factory=list, description="数据行（不含表头）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_id": "page1_table0",
                "page_number": 1,
                "markdown_content": "| Header1 | Header2 |\n|---------|---------|",
                "row_count": 5,
                "col_count": 2,
                "headers": ["Header1", "Header2"],
                "data": [["Cell1", "Cell2"], ["Cell3", "Cell4"]]
            }
        }


class TableExtractorOutput(BaseModel):
    """TableExtractor 输出结果"""
    file_path: str = Field(..., description="源文件路径")
    total_pages: int = Field(..., description="PDF 总页数")
    processed_pages: List[int] = Field(..., description="实际处理的页码列表")
    tables: List[TableData] = Field(default_factory=list, description="提取的表格列表")
    table_count: int = Field(..., description="总表格数")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外元数据: 提取耗时、错误页码等"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/path/to/document.pdf",
                "total_pages": 10,
                "processed_pages": [1, 2, 3],
                "tables": [],
                "table_count": 5,
                "metadata": {"extraction_time_ms": 1250}
            }
        }


# ========== Skill 实现 ==========

class TableExtractor:
    """
    表格提取 Skill
    
    职责:
        - 使用 pdfplumber 从 PDF 提取表格
        - 将表格转换为 Markdown 格式（便于 LLM 理解）
        - 提取表头和数据行，便于结构化处理
    
    特点:
        - 独立的表格提取逻辑，不依赖其他 Engine
        - 支持自定义提取选项
        - 完整的错误处理和日志
    
    示例:
        >>> extractor = TableExtractor()
        >>> input_data = TableExtractorInput(file_path="doc.pdf")
        >>> output = extractor.execute(input_data)
        >>> print(f"提取了 {output.table_count} 个表格")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 TableExtractor
        
        Args:
            config: 可选配置字典
                - default_extract_options: 默认的 pdfplumber 提取选项
        """
        self.config = config or {}
        self.default_extract_options = self.config.get("default_extract_options", {})
        
        logger.info(
            "TableExtractor initialized",
            extra={"config": self.config}
        )
    
    def execute(self, input_data: TableExtractorInput) -> TableExtractorOutput:
        """
        执行表格提取
        
        Args:
            input_data: 输入参数（Pydantic 模型）
        
        Returns:
            TableExtractorOutput: 提取结果
        
        Raises:
            FileNotFoundError: 文件不存在时
            ValueError: 输入参数无效时
            RuntimeError: PDF 处理失败时
        """
        import time
        start_time = time.time()
        
        logger.info(
            "TableExtractor execution started",
            extra={
                "file_path": input_data.file_path,
                "page_numbers": input_data.page_numbers
            }
        )
        
        try:
            # 1. 验证输入
            if not self.validate(input_data):
                raise ValueError("输入数据验证失败")
            
            # 2. 打开 PDF 文件
            file_path = Path(input_data.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {input_data.file_path}")
            
            # 3. 提取表格
            tables = []
            total_pages = 0
            processed_pages = []
            error_pages = []
            
            with pdfplumber.open(str(file_path)) as pdf:
                total_pages = len(pdf.pages)
                
                # 确定要处理的页码
                if input_data.page_numbers:
                    # 验证页码范围
                    pages_to_process = [
                        p for p in input_data.page_numbers 
                        if 1 <= p <= total_pages
                    ]
                else:
                    pages_to_process = list(range(1, total_pages + 1))
                
                # 逐页提取
                for page_num in pages_to_process:
                    try:
                        page = pdf.pages[page_num - 1]  # pdfplumber 从0开始索引
                        page_tables = self._extract_tables_from_page(
                            page, 
                            page_num,
                            input_data.extract_options
                        )
                        tables.extend(page_tables)
                        processed_pages.append(page_num)
                    except Exception as e:
                        logger.warning(
                            f"提取第 {page_num} 页表格失败",
                            error=str(e)
                        )
                        error_pages.append(page_num)
            
            # 4. 构建输出
            end_time = time.time()
            extraction_time_ms = int((end_time - start_time) * 1000)
            
            output = TableExtractorOutput(
                file_path=input_data.file_path,
                total_pages=total_pages,
                processed_pages=processed_pages,
                tables=tables,
                table_count=len(tables),
                metadata={
                    "extraction_time_ms": extraction_time_ms,
                    "error_pages": error_pages,
                    "success_rate": len(processed_pages) / len(pages_to_process) 
                                   if pages_to_process else 0
                }
            )
            
            logger.info(
                "TableExtractor execution completed",
                extra={
                    "table_count": output.table_count,
                    "processed_pages": len(processed_pages),
                    "extraction_time_ms": extraction_time_ms
                }
            )
            
            return output
            
        except FileNotFoundError as e:
            logger.error("文件未找到", error=str(e))
            raise
        except ValueError as e:
            logger.error("验证失败", error=str(e))
            raise
        except Exception as e:
            logger.error("表格提取失败", error=str(e))
            raise RuntimeError(f"TableExtractor 执行失败: {str(e)}") from e
    
    def _extract_tables_from_page(
        self,
        page: pdfplumber.pdf.Page,
        page_num: int,
        extract_options: Dict[str, Any]
    ) -> List[TableData]:
        """
        从单个页面提取表格
        
        Args:
            page: pdfplumber Page 对象
            page_num: 页码（从1开始）
            extract_options: 提取选项
        
        Returns:
            List[TableData]: 该页的表格列表
        """
        table_blocks = []
        
        # 合并默认选项和用户选项
        options = {**self.default_extract_options, **extract_options}
        
        # pdfplumber 提取表格
        try:
            tables = page.extract_tables(table_settings=options) if options else page.extract_tables()
        except Exception as e:
            logger.warning(f"pdfplumber 提取表格失败: {e}")
            tables = []
        
        for idx, table in enumerate(tables):
            if not table or len(table) == 0:
                continue
            
            try:
                # 获取表头
                headers = table[0] if table else []
                data_rows = table[1:] if len(table) > 1 else []
                
                # 转换为 Markdown
                markdown = self._table_to_markdown(headers, data_rows)
                
                # 构建 TableData 对象
                # 注意：headers 使用 str(h) 保持与旧实现一致（None -> "None"）
                # data 使用 str(cell) if cell else "" （None -> ""）
                table_data = TableData(
                    table_id=f"page{page_num}_table{idx}",
                    page_number=page_num,
                    markdown_content=markdown,
                    row_count=len(table),
                    col_count=len(headers) if headers else 0,
                    headers=[str(h) for h in headers] if headers else [],
                    data=[[str(cell) if cell else "" for cell in row] for row in data_rows]
                )
                table_blocks.append(table_data)
                
            except Exception as e:
                logger.warning(
                    f"格式化第 {page_num} 页第 {idx} 个表格失败",
                    error=str(e)
                )
                continue
        
        logger.debug(f"从第 {page_num} 页提取 {len(table_blocks)} 个表格")
        return table_blocks
    
    def _table_to_markdown(self, headers: List, data: List[List]) -> str:
        """
        将表格转换为 Markdown 格式
        
        Args:
            headers: 表头列表
            data: 数据行列表
        
        Returns:
            str: Markdown 格式的表格
        
        注意:
            - 保留语义结构，便于 LLM 理解
            - 自动处理 None 值和列数不匹配
            - headers 使用 str(h) 保持与旧实现一致
        """
        if not headers:
            return ""
        
        # 清理 None 值（与旧实现保持一致）
        headers = [str(h) for h in headers]
        
        # 构建 Markdown 表格
        markdown_lines = []
        
        # 表头
        markdown_lines.append("| " + " | ".join(headers) + " |")
        
        # 分隔符
        markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # 数据行
        for row in data:
            # 数据行保持旧逻辑：None → 空字符串（与 headers 不同）
            row_clean = [str(cell) if cell else "" for cell in row]
            # 补齐列数
            while len(row_clean) < len(headers):
                row_clean.append("")
            # 截断超出的列
            markdown_lines.append("| " + " | ".join(row_clean[:len(headers)]) + " |")
        
        return "\n".join(markdown_lines)
    
    def validate(self, input_data: TableExtractorInput) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入参数
        
        Returns:
            bool: 验证是否通过
        """
        # 文件路径不能为空
        if not input_data.file_path:
            logger.warning("文件路径为空")
            return False
        
        # 文件必须是 PDF
        if not input_data.file_path.lower().endswith('.pdf'):
            logger.warning("文件不是 PDF 格式")
            return False
        
        # 页码范围验证（如果指定）
        if input_data.page_numbers:
            if any(p < 1 for p in input_data.page_numbers):
                logger.warning("页码必须 >= 1")
                return False
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        返回 Skill 元数据
        
        Returns:
            dict: 包含名称、版本、描述等信息
        """
        return {
            "name": self.__class__.__name__,
            "version": "1.0.0",
            "description": "从 PDF 提取表格并转换为 Markdown 格式",
            "source": "migrated from agents/preprocessor.py",
            "dependencies": ["pdfplumber"],
            "config": self.config
        }


# ========== 使用示例 ==========

if __name__ == "__main__":
    """
    测试 TableExtractor 功能
    
    运行: python -m skills.table_extractor
    """
    import sys
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python -m skills.table_extractor <pdf_file_path> [page_numbers...]")
        print("示例: python -m skills.table_extractor document.pdf 1 2 3")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    page_nums = [int(p) for p in sys.argv[2:]] if len(sys.argv) > 2 else None
    
    # 创建 Skill 实例
    extractor = TableExtractor()
    
    # 准备输入数据
    input_data = TableExtractorInput(
        file_path=pdf_path,
        page_numbers=page_nums
    )
    
    # 执行提取
    try:
        output = extractor.execute(input_data)
        
        print(f"\n✅ 表格提取成功!")
        print(f"   文件: {output.file_path}")
        print(f"   总页数: {output.total_pages}")
        print(f"   处理页数: {len(output.processed_pages)}")
        print(f"   提取表格数: {output.table_count}")
        print(f"   耗时: {output.metadata.get('extraction_time_ms')}ms")
        
        if output.tables:
            print(f"\n📊 表格详情:")
            for table in output.tables[:3]:  # 只显示前3个
                print(f"   - {table.table_id}: {table.row_count}行 x {table.col_count}列")
                print(f"     表头: {table.headers}")
                if len(output.tables) > 3:
                    print(f"   ... 还有 {len(output.tables) - 3} 个表格")
                    break
        
        # 显示元数据
        metadata = extractor.get_metadata()
        print(f"\n📊 Skill 元数据:")
        for key, value in metadata.items():
            if key != "config":
                print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
