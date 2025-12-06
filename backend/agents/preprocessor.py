"""
Layer 1: 预处理代理（Preprocessor Agent）
负责文档结构化解析，使用pdfplumber增强表格提取
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import pdfplumber
import re
from pydantic import BaseModel, Field
from datetime import datetime

from core.logger import logger


# ========== Pydantic模型 ==========

class TextBlock(BaseModel):
    """文本块模型"""
    block_id: str
    block_type: str  # paragraph, table, title, list
    content: str
    page_number: int
    position: Dict[str, float] = Field(default_factory=dict)  # {x0, y0, x1, y1}
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TableBlock(BaseModel):
    """表格块模型"""
    table_id: str
    page_number: int
    markdown_content: str  # 表格转Markdown
    row_count: int
    col_count: int
    headers: List[str] = Field(default_factory=list)
    data: List[List[str]] = Field(default_factory=list)


class ChapterNode(BaseModel):
    """章节节点模型"""
    chapter_id: str
    level: int  # 1, 2, 3...
    title: str
    content: str = ""
    children: List['ChapterNode'] = Field(default_factory=list)
    start_page: int
    end_page: Optional[int] = None


class DocumentStructure(BaseModel):
    """文档结构化输出"""
    file_path: str
    total_pages: int
    text_blocks: List[TextBlock]
    table_blocks: List[TableBlock]
    chapter_tree: List[ChapterNode]
    keywords: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


# ========== 预处理代理 ==========

class PreprocessorAgent:
    """
    预处理代理 - Layer 1
    
    核心功能：
    1. PDF文档解析（pdfplumber）
    2. 表格提取并转Markdown
    3. 章节结构识别
    4. 关键词提取
    5. 文本块分割
    """
    
    def __init__(self):
        """初始化预处理代理"""
        # 章节标题正则模式
        self.chapter_patterns = [
            r'^第[一二三四五六七八九十\d]+章\s+(.+)',
            r'^第[一二三四五六七八九十\d]+节\s+(.+)',
            r'^[\d]+\.[\d]*\s+(.+)',
            r'^[一二三四五六七八九十]+、\s+(.+)',
        ]
        
        # 关键词模式（投标领域）
        self.keyword_patterns = [
            r'必须|强制|禁止',
            r'资质|证书|认证',
            r'ISO\s*\d+',
            r'业绩|案例',
            r'技术参数|规格|指标',
            r'价格|报价|金额',
            r'评分|得分|打分',
        ]
        
        logger.info("PreprocessorAgent initialized")
    
    # ========== 核心方法 ==========
    
    async def process_document(self, file_path: str) -> DocumentStructure:
        """
        处理整个文档
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            文档结构化对象
        """
        logger.info(f"Processing document: {file_path}")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        text_blocks = []
        table_blocks = []
        
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"Total pages: {total_pages}")
            
            for page_num, page in enumerate(pdf.pages, start=1):
                # 提取文本块
                page_text_blocks = await self._extract_text_blocks(page, page_num)
                text_blocks.extend(page_text_blocks)
                
                # 提取表格
                page_table_blocks = await self._extract_tables(page, page_num)
                table_blocks.extend(page_table_blocks)
        
        # 构建章节树
        chapter_tree = await self._build_chapter_tree(text_blocks)
        
        # 提取关键词
        all_text = "\n".join([b.content for b in text_blocks])
        keywords = await self._extract_keywords(all_text)
        
        result = DocumentStructure(
            file_path=file_path,
            total_pages=total_pages,
            text_blocks=text_blocks,
            table_blocks=table_blocks,
            chapter_tree=chapter_tree,
            keywords=keywords,
            metadata={
                "text_block_count": len(text_blocks),
                "table_count": len(table_blocks),
                "chapter_count": len(chapter_tree)
            }
        )
        
        logger.info(f"Document processed: {len(text_blocks)} text blocks, {len(table_blocks)} tables")
        return result
    
    async def _extract_text_blocks(
        self, 
        page: pdfplumber.pdf.Page, 
        page_num: int
    ) -> List[TextBlock]:
        """提取文本块"""
        blocks = []
        
        # 提取文本
        text = page.extract_text()
        if not text:
            return blocks
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        
        for idx, para in enumerate(paragraphs):
            if not para.strip():
                continue
            
            # 判断文本类型
            block_type = self._classify_text_type(para)
            
            block = TextBlock(
                block_id=f"page{page_num}_block{idx}",
                block_type=block_type,
                content=para.strip(),
                page_number=page_num,
                position={},  # pdfplumber暂不提供精确位置
                metadata={"length": len(para)}
            )
            blocks.append(block)
        
        return blocks
    
    async def _extract_tables(
        self, 
        page: pdfplumber.pdf.Page, 
        page_num: int
    ) -> List[TableBlock]:
        """
        提取表格并转换为Markdown
        关键：使用pdfplumber的表格识别能力
        """
        table_blocks = []
        
        # pdfplumber提取表格
        tables = page.extract_tables()
        
        for idx, table in enumerate(tables):
            if not table or len(table) == 0:
                continue
            
            # 获取表头
            headers = table[0] if table else []
            data_rows = table[1:] if len(table) > 1 else []
            
            # 转换为Markdown
            markdown = self._table_to_markdown(headers, data_rows)
            
            table_block = TableBlock(
                table_id=f"page{page_num}_table{idx}",
                page_number=page_num,
                markdown_content=markdown,
                row_count=len(table),
                col_count=len(headers) if headers else 0,
                headers=[str(h) for h in headers] if headers else [],
                data=[[str(cell) if cell else "" for cell in row] for row in data_rows]
            )
            table_blocks.append(table_block)
        
        logger.debug(f"Extracted {len(table_blocks)} tables from page {page_num}")
        return table_blocks
    
    def _table_to_markdown(self, headers: List[str], data: List[List[str]]) -> str:
        """
        将表格转换为Markdown格式
        保留语义结构，便于LLM理解
        """
        if not headers:
            return ""
        
        # 清理None值
        headers = [str(h) if h else "" for h in headers]
        
        # 构建Markdown表格
        markdown_lines = []
        
        # 表头
        markdown_lines.append("| " + " | ".join(headers) + " |")
        
        # 分隔符
        markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # 数据行
        for row in data:
            row_clean = [str(cell) if cell else "" for cell in row]
            # 补齐列数
            while len(row_clean) < len(headers):
                row_clean.append("")
            markdown_lines.append("| " + " | ".join(row_clean[:len(headers)]) + " |")
        
        return "\n".join(markdown_lines)
    
    async def _build_chapter_tree(self, text_blocks: List[TextBlock]) -> List[ChapterNode]:
        """
        构建章节树
        识别标题层级并组织为树形结构
        """
        chapters = []
        current_chapter = None
        
        for block in text_blocks:
            if block.block_type == "title":
                # 检测章节级别
                level = self._detect_chapter_level(block.content)
                
                chapter = ChapterNode(
                    chapter_id=block.block_id,
                    level=level,
                    title=block.content,
                    start_page=block.page_number,
                    end_page=block.page_number
                )
                
                if level == 1:
                    chapters.append(chapter)
                    current_chapter = chapter
                elif level == 2 and current_chapter:
                    current_chapter.children.append(chapter)
            
            elif current_chapter:
                # 添加内容到当前章节
                current_chapter.content += "\n" + block.content
                current_chapter.end_page = block.page_number
        
        return chapters
    
    def _classify_text_type(self, text: str) -> str:
        """分类文本类型"""
        text = text.strip()
        
        # 检查是否为标题
        for pattern in self.chapter_patterns:
            if re.match(pattern, text):
                return "title"
        
        # 检查是否为列表
        if re.match(r'^[\d]+\.', text) or re.match(r'^[一二三四五六七八九十]+、', text):
            return "list"
        
        # 默认为段落
        return "paragraph"
    
    def _detect_chapter_level(self, title: str) -> int:
        """检测章节级别"""
        if re.match(r'^第[一二三四五六七八九十\d]+章', title):
            return 1
        elif re.match(r'^第[一二三四五六七八九十\d]+节', title):
            return 2
        elif re.match(r'^[\d]+\.[\d]+', title):
            return 2
        elif re.match(r'^[\d]+\.', title):
            return 1
        else:
            return 1
    
    async def _extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """
        提取关键词
        基于规则的简单实现，后续可集成spaCy NLP
        """
        keywords = set()
        
        # 基于正则模式提取
        for pattern in self.keyword_patterns:
            matches = re.findall(pattern, text)
            keywords.update([m.strip() for m in matches if m.strip()])
        
        # 提取高频词（简化版）
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        word_freq = {}
        for word in words:
            if len(word) >= 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 取高频词
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_k]
        keywords.update([w[0] for w in top_words])
        
        return list(keywords)[:top_k]
    
    # ========== 辅助方法 ==========
    
    async def extract_specific_chapter(
        self, 
        file_path: str, 
        chapter_title: str
    ) -> Optional[ChapterNode]:
        """提取特定章节"""
        doc_structure = await self.process_document(file_path)
        
        for chapter in doc_structure.chapter_tree:
            if chapter_title in chapter.title:
                return chapter
            for child in chapter.children:
                if chapter_title in child.title:
                    return child
        
        return None
    
    async def get_tables_from_page_range(
        self, 
        file_path: str, 
        start_page: int, 
        end_page: int
    ) -> List[TableBlock]:
        """获取指定页码范围的表格"""
        doc_structure = await self.process_document(file_path)
        
        return [
            table for table in doc_structure.table_blocks
            if start_page <= table.page_number <= end_page
        ]
