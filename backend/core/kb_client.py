"""
知识库客户端实现
所有 MCP 通过这个客户端查询知识库的结构化数据

提供的方法：
- get_file_metadata(file_id) -> FileMetadata
- get_chapters(file_id) -> List[ChapterData]
- get_chapter(chapter_id) -> ChapterData
- compare_chapters(ch1_id, ch2_id) -> 差异信息
- compare_files(f1_id, f2_id) -> 差异信息
- get_chapter_structure(chapter_id) -> 结构信息
- extract_keywords(chapter_id, top_n) -> 关键词列表
- search_in_file(file_id, keyword) -> 搜索结果
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

# 导入数据库模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import db
from core.logger import logger

# 导入共享的数据模型
shared_path = str(Path(__file__).parent.parent.parent / 'mcp-servers' / 'shared')
sys.path.insert(0, shared_path)
from kb_interface import ChapterData, FileMetadata


class KBClient:
    """知识库客户端的具体实现"""
    
    def __init__(self):
        """初始化知识库客户端"""
        self.db = db
        logger.info("KBClient initialized")
    
    async def get_file_metadata(self, file_id: str) -> FileMetadata:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            FileMetadata 对象
            
        Raises:
            ValueError: 文件不存在
        """
        file_info = self.db.query_one(
            """
            SELECT id, filename, filetype, 
                   (SELECT COUNT(*) FROM chapters WHERE file_id = uploaded_files.id) as total_chapters,
                   0 as total_pages,
                   created_at as uploaded_at,
                   status as processing_status
            FROM uploaded_files
            WHERE id = %s
            """,
            (file_id,)
        )
        
        if not file_info:
            raise ValueError(f"File {file_id} not found")
        
        return FileMetadata(
            id=file_info['id'],
            filename=file_info['filename'],
            filetype=file_info['filetype'],
            file_size=0,
            total_chapters=file_info['total_chapters'],
            total_pages=file_info['total_pages'],
            uploaded_at=file_info['uploaded_at'],
            processed_at=file_info.get('processed_at'),
            processing_status=file_info.get('processing_status', 'unknown'),
            tags=file_info.get('tags', []),
            is_tender=file_info.get('is_tender')
        )
    
    async def get_chapters(self, file_id: str) -> List[ChapterData]:
        """
        获取文件的所有章节
        
        Args:
            file_id: 文件ID
            
        Returns:
            章节列表
            
        Raises:
            ValueError: 文件不存在
        """
        # 先验证文件存在
        await self.get_file_metadata(file_id)
        
        chapters = self.db.query(
            """
            SELECT id, file_id, chapter_number, chapter_title, chapter_level,
                   position_order, content, structure_data
            FROM chapters
            WHERE file_id = %s
            ORDER BY position_order ASC
            """,
            (file_id,)
        )
        
        result = []
        for ch in chapters:
            chapter_data = ChapterData(
                id=ch['id'],
                file_id=ch['file_id'],
                chapter_number=ch['chapter_number'],
                chapter_title=ch['chapter_title'],
                chapter_level=ch['chapter_level'],
                position_order=ch['position_order'],
                content=ch['content'],
                structure_data=ch.get('structure_data'),
            )
            
            # 附加提取的元素（如果有）
            chapter_data.keywords = await self._get_cached_keywords(ch['id'])
            
            result.append(chapter_data)
        
        return result
    
    async def get_chapter(self, chapter_id: str) -> ChapterData:
        """
        获取单个章节的详细数据
        
        Args:
            chapter_id: 章节ID
            
        Returns:
            章节数据
            
        Raises:
            ValueError: 章节不存在
        """
        chapter = self.db.query_one(
            """
            SELECT id, file_id, chapter_number, chapter_title, chapter_level,
                   position_order, content, structure_data
            FROM chapters
            WHERE id = %s
            """,
            (chapter_id,)
        )
        
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")
        
        chapter_data = ChapterData(
            id=chapter['id'],
            file_id=chapter['file_id'],
            chapter_number=chapter['chapter_number'],
            chapter_title=chapter['chapter_title'],
            chapter_level=chapter['chapter_level'],
            position_order=chapter['position_order'],
            content=chapter['content'],
            structure_data=chapter.get('structure_data'),
        )
        
        # 附加提取的元素
        chapter_data.keywords = await self._get_cached_keywords(chapter_id)
        chapter_data.tables = await self._extract_tables(chapter_id)
        chapter_data.lists = await self._extract_lists(chapter_id)
        
        return chapter_data
    
    async def compare_chapters(
        self,
        chapter_id_1: str,
        chapter_id_2: str
    ) -> Dict[str, Any]:
        """
        比较两个章节的差异
        
        Args:
            chapter_id_1: 第一个章节ID（如招标）
            chapter_id_2: 第二个章节ID（如投标）
            
        Returns:
            差异分析结果
        """
        ch1 = await self.get_chapter(chapter_id_1)
        ch2 = await self.get_chapter(chapter_id_2)
        
        return {
            'chapter_1': {
                'id': ch1.id,
                'title': ch1.chapter_title,
                'level': ch1.chapter_level,
                'content_length': len(ch1.content),
                'keywords': ch1.keywords or []
            },
            'chapter_2': {
                'id': ch2.id,
                'title': ch2.chapter_title,
                'level': ch2.chapter_level,
                'content_length': len(ch2.content),
                'keywords': ch2.keywords or []
            },
            'differences': {
                'title_changed': ch1.chapter_title != ch2.chapter_title,
                'level_changed': ch1.chapter_level != ch2.chapter_level,
                'content_length_ratio': len(ch2.content) / max(len(ch1.content), 1),
                'keyword_diff': {
                    'common': set(ch1.keywords or []) & set(ch2.keywords or []),
                    'only_in_1': set(ch1.keywords or []) - set(ch2.keywords or []),
                    'only_in_2': set(ch2.keywords or []) - set(ch1.keywords or [])
                }
            }
        }
    
    async def compare_files(
        self,
        file_id_1: str,
        file_id_2: str
    ) -> Dict[str, Any]:
        """
        比较两个文件的全局差异
        
        Args:
            file_id_1: 文件ID 1（如招标）
            file_id_2: 文件ID 2（如投标）
            
        Returns:
            差异分析结果
        """
        file1 = await self.get_file_metadata(file_id_1)
        file2 = await self.get_file_metadata(file_id_2)
        
        chapters1 = await self.get_chapters(file_id_1)
        chapters2 = await self.get_chapters(file_id_2)
        
        # 按章节标题匹配
        title_map = {}
        for ch1 in chapters1:
            for ch2 in chapters2:
                if ch1.chapter_title == ch2.chapter_title:
                    if ch1.chapter_title not in title_map:
                        title_map[ch1.chapter_title] = []
                    title_map[ch1.chapter_title].append({
                        'ch1': ch1,
                        'ch2': ch2
                    })
        
        # 计算统计数据
        matched_chapters = len(title_map)
        unmatched_in_1 = len([ch for ch in chapters1 if ch.chapter_title not in title_map])
        unmatched_in_2 = len([ch for ch in chapters2 if ch.chapter_title not in title_map])
        
        return {
            'file_1': {
                'id': file1.id,
                'filename': file1.filename,
                'total_chapters': file1.total_chapters
            },
            'file_2': {
                'id': file2.id,
                'filename': file2.filename,
                'total_chapters': file2.total_chapters
            },
            'comparison': {
                'matched_chapters': matched_chapters,
                'unmatched_in_file_1': unmatched_in_1,
                'unmatched_in_file_2': unmatched_in_2,
                'structure_similarity': matched_chapters / max(
                    len(chapters1), len(chapters2), 1
                )
            }
        }
    
    async def get_chapter_structure(self, chapter_id: str) -> Dict[str, Any]:
        """
        获取章节的结构（标题层级、小节等）
        
        Args:
            chapter_id: 章节ID
            
        Returns:
            结构信息
        """
        chapter = await self.get_chapter(chapter_id)
        
        # 从内容提取小节标题（简单实现）
        sections = self._extract_sections(chapter.content)
        
        return {
            'chapter_id': chapter_id,
            'title': chapter.chapter_title,
            'level': chapter.chapter_level,
            'sections': sections,
            'hierarchy_depth': self._calculate_hierarchy_depth(chapter.content),
            'has_table': chapter.structure_data and 'tables' in chapter.structure_data,
            'has_list': chapter.structure_data and 'lists' in chapter.structure_data,
        }
    
    async def extract_keywords(
        self,
        chapter_id: str,
        top_n: int = 20
    ) -> List[str]:
        """
        提取章节的关键词
        
        Args:
            chapter_id: 章节ID
            top_n: 返回前 N 个关键词
            
        Returns:
            关键词列表
        """
        keywords = await self._get_cached_keywords(chapter_id, top_n)
        if keywords:
            return keywords
        
        # 如果缓存中没有，进行提取（简单频率统计）
        chapter = await self.get_chapter(chapter_id)
        keywords = self._extract_keywords_simple(chapter.content, top_n)
        
        # 缓存结果
        await self._cache_keywords(chapter_id, keywords)
        
        return keywords
    
    async def search_in_file(
        self,
        file_id: str,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """
        在文件中搜索关键词
        
        Args:
            file_id: 文件ID
            keyword: 关键词
            
        Returns:
            包含关键词的片段列表
        """
        chapters = await self.get_chapters(file_id)
        results = []
        
        for chapter in chapters:
            # 在内容中查找关键词
            occurrences = []
            for i, line in enumerate(chapter.content.split('\n')):
                if keyword.lower() in line.lower():
                    occurrences.append({
                        'line_number': i,
                        'text': line.strip()[:100]  # 截断至 100 字符
                    })
            
            if occurrences:
                results.append({
                    'chapter_id': chapter.id,
                    'chapter_title': chapter.chapter_title,
                    'occurrences': occurrences
                })
        
        return results
    
    # ============================================================================
    # 辅助方法
    # ============================================================================
    
    async def _get_cached_keywords(
        self,
        chapter_id: str,
        top_n: int = 20
    ) -> Optional[List[str]]:
        """从缓存或数据库获取关键词"""
        # 简单实现：可以后续集成 Redis 缓存
        return None  # 返回 None 表示需要重新提取
    
    async def _cache_keywords(
        self,
        chapter_id: str,
        keywords: List[str]
    ) -> None:
        """缓存关键词"""
        # 简单实现：可以后续集成 Redis 缓存
        pass
    
    async def _extract_tables(self, chapter_id: str) -> List[Dict[str, Any]]:
        """提取章节中的表格"""
        # 从 structure_data 中获取表格（如果有）
        chapter = self.db.query_one(
            "SELECT structure_data FROM chapters WHERE id = %s",
            (chapter_id,)
        )
        
        if chapter and chapter['structure_data']:
            return chapter['structure_data'].get('tables', [])
        
        return []
    
    async def _extract_lists(self, chapter_id: str) -> List[Dict[str, Any]]:
        """提取章节中的列表"""
        # 从 structure_data 中获取列表（如果有）
        chapter = self.db.query_one(
            "SELECT structure_data FROM chapters WHERE id = %s",
            (chapter_id,)
        )
        
        if chapter and chapter['structure_data']:
            return chapter['structure_data'].get('lists', [])
        
        return []
    
    def _extract_sections(self, content: str) -> List[str]:
        """从内容提取小节标题"""
        sections = []
        
        # 简单实现：查找以数字或特定模式开头的行
        for line in content.split('\n'):
            line = line.strip()
            # 匹配 "1.", "1.1", "一、" 等模式
            if re.match(r'^(\d+\.?|[一二三四五六七八九十]+)[、\.]', line):
                sections.append(line[:50])  # 截断至 50 字符
        
        return sections
    
    def _calculate_hierarchy_depth(self, content: str) -> int:
        """计算内容的层级深度"""
        max_depth = 0
        
        for line in content.split('\n'):
            # 根据缩进或标题标记计算深度
            if line.startswith('####'):
                max_depth = max(max_depth, 4)
            elif line.startswith('###'):
                max_depth = max(max_depth, 3)
            elif line.startswith('##'):
                max_depth = max(max_depth, 2)
            elif line.startswith('#'):
                max_depth = max(max_depth, 1)
        
        return max_depth or 1
    
    def _extract_keywords_simple(
        self,
        content: str,
        top_n: int = 20
    ) -> List[str]:
        """
        简单的关键词提取（基于词频）
        
        更复杂的实现可以使用 NLP 库如 jieba
        """
        # 分割文本为词
        words = re.findall(r'\w+', content.lower())
        
        # 过滤停用词（简单列表）
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was',
            '的', '了', '在', '是', '为', '有', '等', '与', '及', '以'
        }
        
        words = [w for w in words if w not in stopwords and len(w) > 1]
        
        # 词频统计
        from collections import Counter
        word_freq = Counter(words)
        
        # 返回频率最高的 top_n 个词
        return [word for word, _ in word_freq.most_common(top_n)]


# 全局实例
_kb_client_instance: Optional[KBClient] = None


def get_kb_client() -> KBClient:
    """获取知识库客户端实例（单例）"""
    global _kb_client_instance
    
    if _kb_client_instance is None:
        _kb_client_instance = KBClient()
    
    return _kb_client_instance
