"""
文档解析引擎
支持PDF和Word文档的解析,自动分割章节
"""
from pypdf import PdfReader
import docx
import re
import uuid
import os
import json
from typing import Dict, List, Optional
from database import db


class ParseEngine:
    """文档解析引擎"""
    
    def __init__(self):
        """初始化解析引擎"""
        self.db = db
        self.chapter_patterns = [
            r'^第[一二三四五六七八九十百]+章\s+(.+)$',  # 第一章 标题
            r'^第[一二三四五六七八九十百]+节\s+(.+)$',  # 第一节 标题
            r'^(\d+)\s+(.+)$',  # 1 标题
            r'^(\d+\.\d+)\s+(.+)$',  # 1.1 标题
            r'^(\d+\.\d+\.\d+)\s+(.+)$',  # 1.1.1 标题
        ]
    
    def parse(self, file_path: str, doc_type: str) -> Dict:
        """
        解析文件并存入数据库
        
        Args:
            file_path: 文件路径
            doc_type: 文档类型(tender/proposal/reference)
            
        Returns:
            dict: {file_id, filename, chapters}
        """
        # 1. 提取文本
        if file_path.endswith('.pdf'):
            content = self._parse_pdf(file_path)
        elif file_path.endswith(('.docx', '.doc')):
            content = self._parse_docx(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        # 2. 分割章节
        chapters = self._split_chapters(content)
        
        # 2.1 边界检查:如果没有识别到章节,创建默认章节
        if not chapters:
            chapters = [{
                'chapter_number': '1',
                'chapter_title': '全文',
                'chapter_level': 1,
                'content': content
            }]
        
        # 3. 保存到数据库
        file_id = self._save_to_db(file_path, doc_type, content, chapters)
        
        return {
            'file_id': file_id,
            'filename': os.path.basename(file_path),
            'total_chapters': len(chapters),
            'chapters': chapters
        }
    
    def _parse_pdf(self, file_path: str) -> str:
        """
        解析PDF文件
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            str: 提取的文本内容
        """
        reader = PdfReader(file_path)
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return '\n'.join(text_parts)
    
    def _parse_docx(self, file_path: str) -> str:
        """
        解析Word文档
        
        Args:
            file_path: Word文件路径
            
        Returns:
            str: 提取的文本内容
        """
        doc = docx.Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return '\n'.join(text_parts)
    
    def _split_chapters(self, content: str) -> List[Dict]:
        """
        分割章节
        
        Args:
            content: 文档全文
            
        Returns:
            list: 章节列表,每个章节包含 {chapter_number, chapter_title, content, level}
        """
        lines = content.split('\n')
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是章节标题
            is_chapter, chapter_info = self._is_chapter_title(line)
            
            if is_chapter:
                # 保存上一章节
                if current_chapter:
                    current_chapter['content'] = '\n'.join(current_content).strip()
                    chapters.append(current_chapter)
                
                # 开始新章节
                current_chapter = {
                    'chapter_number': chapter_info['number'],
                    'chapter_title': chapter_info['title'],
                    'chapter_level': chapter_info['level'],
                    'content': ''
                }
                current_content = []
            else:
                # 累积章节内容
                if current_chapter:
                    current_content.append(line)
        
        # 保存最后一章
        if current_chapter:
            current_chapter['content'] = '\n'.join(current_content).strip()
            chapters.append(current_chapter)
        
        return chapters
    
    def _is_chapter_title(self, line: str) -> tuple:
        """
        判断是否是章节标题
        
        Args:
            line: 文本行
            
        Returns:
            tuple: (is_chapter, chapter_info)
        """
        for level, pattern in enumerate(self.chapter_patterns, start=1):
            match = re.match(pattern, line)
            if match:
                if len(match.groups()) == 1:
                    # 第一章 标题 格式
                    return True, {
                        'number': match.group(0).split()[0],
                        'title': match.group(1),
                        'level': level
                    }
                elif len(match.groups()) == 2:
                    # 1 标题 或 1.1 标题 格式
                    return True, {
                        'number': match.group(1),
                        'title': match.group(2),
                        'level': level
                    }
        
        return False, {}
    
    def _save_to_db(self, file_path: str, doc_type: str, content: str, chapters: List[Dict]) -> str:
        """
        保存文件和章节到数据库
        
        Args:
            file_path: 文件路径
            doc_type: 文档类型
            content: 全文内容
            chapters: 章节列表
            
        Returns:
            str: 文件ID
        """
        filename = os.path.basename(file_path)
        filetype = os.path.splitext(filename)[1][1:]  # 去掉点号
        
        # 1. 插入文件记录
        file_id = self.db.execute("""
            INSERT INTO files (filename, filepath, filetype, doc_type, content, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (filename, file_path, filetype, doc_type, content, json.dumps({'total_chapters': len(chapters)})))
        
        # 2. 批量插入章节
        for idx, chapter in enumerate(chapters, start=1):
            self.db.execute("""
                INSERT INTO chapters (
                    file_id, chapter_number, chapter_title, chapter_level, 
                    content, position_order, structure_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                file_id,
                chapter['chapter_number'],
                chapter['chapter_title'],
                chapter['chapter_level'],
                chapter['content'],
                idx,
                json.dumps({'word_count': len(chapter['content'])})
            ))
        
        return file_id
