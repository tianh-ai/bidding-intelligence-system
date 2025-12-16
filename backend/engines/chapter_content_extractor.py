"""
增强型章节内容提取器
功能：
1. 识别章节标题
2. 根据标题位置切分章节内容
3. 使用Ollama辅助理解章节边界（可选）
"""

import re
from typing import List, Dict, Optional, Tuple
import asyncio


class ChapterContentExtractor:
    """章节内容提取器 - 带内容分段"""
    
    # 中文数字映射
    CHINESE_NUM_MAP = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
        '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
    }
    
    def __init__(self, use_ollama: bool = False):
        """
        初始化提取器
        
        Args:
            use_ollama: 是否使用Ollama辅助理解章节边界
        """
        self.use_ollama = use_ollama
        
        # 编译所有正则模式
        self.patterns = {
            'part': re.compile(r'^第([一二三四五])部分[\s　]*(.+)$'),
            'chinese': re.compile(r'^([一二三四五六七八九十]+)、[\s　]*(.+)$'),
            'main_chapter': re.compile(r'^(\d+)\.[\s　]*(.+)$'),
            'level2': re.compile(r'^(\d+)\.(\d+)[\s　]*(.+)$'),
            'level3': re.compile(r'^(\d+)\.(\d+)\.(\d+)[\s　]*(.+)$'),
            'level4': re.compile(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)[\s　]*(.+)$'),
            'attachment': re.compile(r'^附件(\d+)[：:][\s　]*(.+)$'),
            'attachment_sub': re.compile(r'^(\d+)-(\d+)[：:][\s　]*(.+)$'),
        }
    
    def extract_chapters_with_content(self, content: str) -> List[Dict]:
        """
        从文档内容中提取章节结构和内容
        
        Returns:
            List[Dict]: [
                {
                    'chapter_number': str,
                    'chapter_title': str,
                    'chapter_level': int,
                    'content': str,  # 章节正文内容
                    'start_line': int,  # 起始行号
                    'end_line': int,  # 结束行号
                },
                ...
            ]
        """
        lines = content.split('\n')
        chapters = []
        chapter_lines = []  # 存储每个章节的(章节信息, 行号)
        
        # 第一遍：识别所有章节标题及其位置
        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped or len(line_stripped) < 2:
                continue
            
            chapter_info = self._match_chapter_title(line_stripped)
            if chapter_info:
                chapter_lines.append((chapter_info, line_idx))
        
        # 第二遍：根据章节位置切分内容
        for i, (chapter_info, start_line) in enumerate(chapter_lines):
            # 确定章节内容的结束位置（下一个章节的起始位置）
            if i < len(chapter_lines) - 1:
                next_chapter_start = chapter_lines[i + 1][1]
                end_line = next_chapter_start
            else:
                end_line = len(lines)
            
            # 提取章节内容（跳过标题行）
            content_lines = []
            for line_idx in range(start_line + 1, end_line):
                line_text = lines[line_idx].strip()
                # 过滤空行和明显的页眉页脚
                if line_text and not self._is_header_footer(line_text):
                    content_lines.append(lines[line_idx])
            
            chapter_content = '\n'.join(content_lines).strip()
            
            # 添加章节信息
            chapters.append({
                'chapter_number': chapter_info['chapter_number'],
                'chapter_title': chapter_info['chapter_title'],
                'chapter_level': chapter_info['chapter_level'],
                'content': chapter_content,
                'start_line': start_line,
                'end_line': end_line,
                'content_length': len(chapter_content),
            })
        
        # 如果没有识别到章节，将整个文档作为一个章节
        if not chapters:
            chapters.append({
                'chapter_number': '1',
                'chapter_title': '全文',
                'chapter_level': 1,
                'content': content,
                'start_line': 0,
                'end_line': len(lines),
                'content_length': len(content),
            })
        
        return chapters
    
    def _match_chapter_title(self, line: str) -> Optional[Dict]:
        """
        匹配章节标题
        
        Returns:
            Dict or None: {chapter_number, chapter_title, chapter_level}
        """
        # 按优先级匹配（从最具体到最一般）
        
        # 1. 四级章节
        match = self.patterns['level4'].match(line)
        if match:
            number = '.'.join(match.groups()[:-1])
            title = match.groups()[-1].strip()
            if self._is_valid_title(title, level=4):
                return {
                    'chapter_number': number,
                    'chapter_title': title,
                    'chapter_level': 5
                }
        
        # 2. 三级章节
        match = self.patterns['level3'].match(line)
        if match:
            number = '.'.join(match.groups()[:-1])
            title = match.groups()[-1].strip()
            if self._is_valid_title(title, level=3):
                return {
                    'chapter_number': number,
                    'chapter_title': title,
                    'chapter_level': 4
                }
        
        # 3. 二级章节
        match = self.patterns['level2'].match(line)
        if match:
            number = '.'.join(match.groups()[:-1])
            title = match.groups()[-1].strip()
            if self._is_valid_title(title, level=2) and title[0] not in '一二三四五六七八九十':
                return {
                    'chapter_number': number,
                    'chapter_title': title,
                    'chapter_level': 3
                }
        
        # 4. 主章节
        match = self.patterns['main_chapter'].match(line)
        if match:
            number = match.group(1)
            title = match.group(2).strip()
            try:
                num_val = int(number)
                if num_val <= 30 and self._is_valid_title(title, level=1) and title[0] not in '一二三四五六七八九十':
                    return {
                        'chapter_number': number,
                        'chapter_title': title,
                        'chapter_level': 2
                    }
            except:
                pass
        
        # 5. 中文编号
        match = self.patterns['chinese'].match(line)
        if match:
            chinese_num = match.group(1)
            title = match.group(2).strip()
            if chinese_num in self.CHINESE_NUM_MAP and self._is_valid_title(title, level=1):
                return {
                    'chapter_number': chinese_num,
                    'chapter_title': title,
                    'chapter_level': 2
                }
        
        # 6. 部分标题
        match = self.patterns['part'].match(line)
        if match:
            part_num_chinese = match.group(1)
            title = match.group(2).strip()
            if part_num_chinese in self.CHINESE_NUM_MAP:
                return {
                    'chapter_number': f"第{part_num_chinese}部分",
                    'chapter_title': title,
                    'chapter_level': 1
                }
        
        # 7. 附件
        match = self.patterns['attachment'].match(line)
        if match:
            att_num = match.group(1)
            title = match.group(2).strip()
            if self._is_valid_title(title, level=1):
                return {
                    'chapter_number': f"附件{att_num}",
                    'chapter_title': title,
                    'chapter_level': 2
                }
        
        # 8. 附件子项
        match = self.patterns['attachment_sub'].match(line)
        if match:
            num1 = match.group(1)
            num2 = match.group(2)
            title = match.group(3).strip()
            if self._is_valid_title(title, level=2):
                return {
                    'chapter_number': f"{num1}-{num2}",
                    'chapter_title': title,
                    'chapter_level': 3
                }
        
        return None
    
    def _is_valid_title(self, title: str, level: int) -> bool:
        """验证标题是否有效"""
        if not title or len(title) < 2:
            return False
        
        # 过滤无效字符
        if title in ['。', '，', '、', '；', '：', '…', '...']:
            return False
        
        # 过滤纯数字+单位
        if len(title) <= 5:
            if any(unit in title for unit in ['元', '米', '天', '年', '月', '日', '吨', '个', '次', '项', '万', '千', '百']):
                return False
        
        # 过滤法律条款片段
        if title.startswith(('款', '条', '项')):
            if '〔' in title or '【' in title or '（' in title:
                return False
        
        # 过滤以括号开头
        if title[0] in ['(', '（', '[', '【', ')', '）', ']', '】']:
            return False
        
        # 过滤页码标记
        if title.startswith('...') or title.endswith('...'):
            return False
        
        # 过滤目录行
        if title.count('.') > 10 or title.count('。') > 5:
            return False
        
        return True
    
    def _is_header_footer(self, line: str) -> bool:
        """判断是否是页眉页脚"""
        # 常见页眉页脚特征
        if len(line) < 3:
            return True
        
        # 纯数字（页码）
        if line.isdigit() and int(line) < 1000:
            return True
        
        # 连续横线或等号（分隔线）
        if all(c in '-=_' for c in line):
            return True
        
        return False
    
    async def refine_with_ollama(self, chapters: List[Dict]) -> List[Dict]:
        """
        使用Ollama辅助优化章节边界
        
        Args:
            chapters: 初步提取的章节列表
            
        Returns:
            优化后的章节列表
        """
        if not self.use_ollama:
            return chapters
        
        try:
            from core.ollama_client import get_ollama_client
            ollama = get_ollama_client()
            
            # 构建提示词
            chapter_summary = "\n".join([
                f"{ch['chapter_number']} {ch['chapter_title']} (内容长度: {ch['content_length']})"
                for ch in chapters
            ])
            
            messages = [{
                "role": "user",
                "content": f"""请检查以下章节划分是否合理，如果发现明显的章节遗漏或错误，请指出：

{chapter_summary}

请简要回答：
1. 章节划分是否合理？
2. 是否有明显遗漏的章节？
3. 是否有需要合并或拆分的章节？"""
            }]
            
            response = await ollama.chat(messages)
            
            # 记录Ollama的建议（暂不自动应用，避免误判）
            for ch in chapters:
                ch['ollama_review'] = response
            
            from core.logger import logger
            logger.info(f"Ollama章节审查: {response[:200]}...")
            
        except Exception as e:
            from core.logger import logger
            logger.warning(f"Ollama辅助失败（使用原始结果）: {e}")
        
        return chapters


# 单例获取函数
_extractor_instance = None

def get_chapter_content_extractor(use_ollama: bool = False) -> ChapterContentExtractor:
    """获取章节内容提取器实例"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = ChapterContentExtractor(use_ollama=use_ollama)
    return _extractor_instance
