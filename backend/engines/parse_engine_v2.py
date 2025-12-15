"""
改进版文档解析引擎 - 支持完整的层级结构
"""

import re
from typing import List, Dict, Optional


class EnhancedChapterExtractor:
    """增强型章节提取器 - 支持多种编号格式和层级"""
    
    # 中文数字映射
    CHINESE_NUM_MAP = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
        '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
        '二十一': 21
    }
    
    def __init__(self):
        # 编译所有正则模式
        self.patterns = {
            # 顶层部分: 第一部分、第二部分、第三部分
            'part': re.compile(r'^第([一二三四五])部分[\s　]*(.+)$'),
            
            # 中文编号: 一、二、三... (合同协议书部分)
            'chinese': re.compile(r'^([一二三四五六七八九十]+)、[\s　]*(.+)$'),
            
            # 阿拉伯数字主章节: 1.一般约定  2.发包人 (注意后面可能有中文无点号)
            'main_chapter': re.compile(r'^(\d+)\.[\s　]*(.+)$'),
            
            # 二级章节: 1.1 词语定义  1.2 语言文字
            'level2': re.compile(r'^(\d+)\.(\d+)[\s　]*(.+)$'),
            
            # 三级章节: 1.1.1 合同  1.1.2 合同当事人
            'level3': re.compile(r'^(\d+)\.(\d+)\.(\d+)[\s　]*(.+)$'),
            
            # 四级章节: 1.1.1.1 合同  1.1.1.2 合同协议书
            'level4': re.compile(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)[\s　]*(.+)$'),
            
            # 附件: 附件1：承包人承揽工程项目一览表
            'attachment': re.compile(r'^附件(\d+)[：:][\s　]*(.+)$'),
            
            # 附件子项: 11-1：材料暂估价表
            'attachment_sub': re.compile(r'^(\d+)-(\d+)[：:][\s　]*(.+)$'),
        }
    
    def extract_chapters(self, content: str) -> List[Dict]:
        """
        从文档内容中提取完整的章节结构
        
        返回格式:
        [
            {'chapter_number': '第一部分', 'chapter_title': '合同协议书', 'chapter_level': 1},
            {'chapter_number': '一', 'chapter_title': '工程概况', 'chapter_level': 2},
            {'chapter_number': '1', 'chapter_title': '一般约定', 'chapter_level': 2},
            {'chapter_number': '1.1', 'chapter_title': '词语定义与解释', 'chapter_level': 3},
            ...
        ]
        
        注意: 每次调用都会重置内部状态，确保解析结果的一致性
        """
        lines = content.split('\n')
        chapters = []
        
        # 状态追踪（这些状态变量不再影响主章节识别，只用于标记当前上下文）
        current_part = None  # 当前部分 (第一部分/第二部分/第三部分)
        in_appendix = False    # 是否进入附件部分
        in_main_chapters = False  # 是否进入主章节区域(第二/三部分)
        
        for line in lines:
            line = line.strip()
            
            if not line or len(line) < 2:
                continue
            
            # 按优先级尝试匹配（从最具体到最一般）
            chapter = None
            
            # 1. 四级章节 (最具体)
            match = self.patterns['level4'].match(line)
            if match:
                number = '.'.join(match.groups()[:-1])
                title = match.groups()[-1].strip()
                if self._is_valid_title(title, level=4):
                    chapter = {
                        'chapter_number': number,
                        'chapter_title': title,
                        'chapter_level': 5  # 四级章节实际是第5层(部分->主章->二级->三级->四级)
                    }
            
            # 2. 三级章节
            if not chapter:
                match = self.patterns['level3'].match(line)
                if match:
                    number = '.'.join(match.groups()[:-1])
                    title = match.groups()[-1].strip()
                    if self._is_valid_title(title, level=3):
                        chapter = {
                            'chapter_number': number,
                            'chapter_title': title,
                            'chapter_level': 4  # 三级章节实际是第4层
                        }
            
            # 3. 二级章节
            if not chapter:
                match = self.patterns['level2'].match(line)
                if match:
                    number = '.'.join(match.groups()[:-1])
                    title = match.groups()[-1].strip()
                    # 排除主章节（如"1.一般约定"会被误匹配为"1.一"）
                    if self._is_valid_title(title, level=2) and not title[0] in '一二三四五六七八九十':
                        chapter = {
                            'chapter_number': number,
                            'chapter_title': title,
                            'chapter_level': 3  # 二级章节实际是第3层
                        }
            
            # 4. 主章节 (1. 2. 3. ...)
            if not chapter:
                match = self.patterns['main_chapter'].match(line)
                if match:
                    number = match.group(1)
                    title = match.group(2).strip()
                    
                    # 验证：主章节编号通常<30，且标题是中文
                    try:
                        num_val = int(number)
                        # 主章节识别条件：
                        # 1. 编号在合理范围内(1-30)
                        # 2. 标题有效
                        # 3. 标题不是纯中文数字（避免和"一、二、三"混淆）
                        if num_val <= 30 and self._is_valid_title(title, level=1) and title[0] not in '一二三四五六七八九十':
                            chapter = {
                                'chapter_number': number,
                                'chapter_title': title,
                                'chapter_level': 2  # 主章节是第2层
                            }
                    except:
                        pass
            
            # 5. 中文编号 (一、二、三...)
            if not chapter:
                match = self.patterns['chinese'].match(line)
                if match:
                    chinese_num = match.group(1)
                    title = match.group(2).strip()
                    
                    if chinese_num in self.CHINESE_NUM_MAP and self._is_valid_title(title, level=1):
                        # 中文编号章节属于"第一部分"的子章节
                        chapter = {
                            'chapter_number': chinese_num,
                            'chapter_title': title,
                            'chapter_level': 2  # 与主章节同级
                        }
            
            # 6. 部分标题 (第X部分)
            if not chapter:
                match = self.patterns['part'].match(line)
                if match:
                    part_num_chinese = match.group(1)
                    title = match.group(2).strip()
                    
                    if part_num_chinese in self.CHINESE_NUM_MAP:
                        part_num = self.CHINESE_NUM_MAP[part_num_chinese]
                        current_part = f"第{part_num_chinese}部分"
                        in_main_chapters = part_num >= 2  # 第二部分开始进入主章节区域
                        
                        chapter = {
                            'chapter_number': current_part,
                            'chapter_title': title,
                            'chapter_level': 1  # 顶层
                        }
            
            # 7. 附件
            if not chapter:
                match = self.patterns['attachment'].match(line)
                if match:
                    att_num = match.group(1)
                    title = match.group(2).strip()
                    
                    if self._is_valid_title(title, level=1):
                        in_appendix = True
                        chapter = {
                            'chapter_number': f"附件{att_num}",
                            'chapter_title': title,
                            'chapter_level': 2  # 与主章节同级
                        }
            
            # 8. 附件子项 (11-1, 11-2)
            if not chapter and in_appendix:
                match = self.patterns['attachment_sub'].match(line)
                if match:
                    num1 = match.group(1)
                    num2 = match.group(2)
                    title = match.group(3).strip()
                    
                    if self._is_valid_title(title, level=2):
                        chapter = {
                            'chapter_number': f"{num1}-{num2}",
                            'chapter_title': title,
                            'chapter_level': 3  # 附件的子项
                        }
            
            # 添加章节
            if chapter:
                chapters.append(chapter)
        
        return chapters
    
    def _is_valid_title(self, title: str, level: int) -> bool:
        """
        验证标题是否有效
        
        Args:
            title: 标题文本
            level: 层级 (1=部分/主章节, 2=二级, 3=三级, 4=四级)
        """
        # 基本验证
        if not title or len(title) < 2:
            return False
        
        # 过滤无效字符
        if title in ['。', '，', '、', '；', '：', '…', '...']:
            return False
        
        # 过滤纯数字+单位 (如"82.76 万元"、"30 天")
        if len(title) <= 5:
            if any(unit in title for unit in ['元', '米', '天', '年', '月', '日', '吨', '个', '次', '项', '万', '千', '百']):
                return False
        
        # 过滤法律条款片段 (如"款〔缺陷责任期〕...")
        if title.startswith(('款', '条', '项')):
            if '〔' in title or '【' in title or '（' in title:
                return False
        
        # 过滤以括号开头的标题
        if title[0] in ['(', '（', '[', '【', ')', '）', ']', '】']:
            return False
        
        # 过滤页码标记 (如"...79", "...80")
        if title.startswith('...') or title.endswith('...'):
            return False
        
        # 过滤包含大量点号的行 (目录行)
        if title.count('.') > 10 or title.count('。') > 5:
            return False
        
        return True


def test_extractor():
    """测试提取器"""
    test_content = """
第一部分合同协议书

一、工程概况
本工程为XXX项目...

二、合同工期
工期为XX天...

三、质量标准
符合国家标准...

第二部分通用合同条款

1.一般约定
1.1 词语定义与解释
1.1.1 合同
1.1.1.1 合同
1.1.1.2 合同协议书

2.发包人
2.1 许可或批准
2.2 发包人代表

3.承包人
3.1 承包人的一般义务
3.2 项目经理

附件1：承包人承揽工程项目一览表
附件2：发包人供应材料设备一览表

附件11：
11-1：材料暂估价表
11-2：工程设备暂估价表
"""
    
    extractor = EnhancedChapterExtractor()
    chapters = extractor.extract_chapters(test_content)
    
    print(f"提取到 {len(chapters)} 个章节:\n")
    for ch in chapters:
        indent = "  " * (ch['chapter_level'] - 1)
        print(f"[L{ch['chapter_level']}] {indent}{ch['chapter_number']} {ch['chapter_title']}")


if __name__ == '__main__':
    test_extractor()
