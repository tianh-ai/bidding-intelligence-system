#!/usr/bin/env python3
"""
验证新版解析器与PDF目录的匹配度
"""

import sys
sys.path.insert(0, '/app')
from engines.parse_engine_v2 import EnhancedChapterExtractor
from engines.parse_engine import ParseEngine

# PDF目录（关键项用于验证）
toc_items = [
    ('第一部分', '合同协议书'),
    ('一', '工程概况'),
    ('二', '合同工期'),
    ('三', '质量标准'),
    ('第二部分', '通用合同条款'),
    ('1', '一般约定'),
    ('2', '发包人'),
    ('3', '承包人'),
    ('1.1', '词语定义与解释'),
    ('1.1.1', '合同'),
    ('1.1.1.1', '合同'),
    ('2.1', '许可或批准'),
    ('2.2', '发包人代表'),
    ('3.1', '承包人的一般义务'),
    ('3.2', '项目经理'),
    ('第三部分', '专用合同条款'),
]

pdf_path = '/app/./uploads/temp/b46e72a8/6f6f42e5-2689-42bc-8bad-32cedf4948cd.pdf'
parser = ParseEngine()
content = parser._parse_pdf(pdf_path)

extractor = EnhancedChapterExtractor()
chapters = extractor.extract_chapters(content)

print('=' * 80)
print('验证新版解析器与PDF目录的匹配')
print('=' * 80)
print()

# 建立查找索引
ch_dict = {ch['chapter_number']: ch for ch in chapters}

success = 0
for num, title in toc_items:
    if num in ch_dict:
        ch = ch_dict[num]
        ch_title = ch['chapter_title'][:40]
        title_match = title in ch['chapter_title'] or ch['chapter_title'] in title or title.replace(' ', '') in ch['chapter_title']
        
        if title_match:
            print(f'✅ {num} {title}')
            print(f'   => {ch["chapter_number"]} {ch_title}')
            success += 1
        else:
            print(f'⚠️  {num} {title}')
            print(f'   => {ch_title} (标题不完全匹配)')
            success += 0.5
    else:
        print(f'❌ {num} {title} (未找到)')

print()
print(f'验证结果: {success}/{len(toc_items)} ({success/len(toc_items)*100:.1f}%)')
print()

# 显示整体结构
print('整体结构预览:')
print('-' * 80)
level_counts = {}
for ch in chapters:
    l = ch['chapter_level']
    level_counts[l] = level_counts.get(l, 0) + 1

for l in sorted(level_counts.keys()):
    print(f'  第{l}层: {level_counts[l]} 个章节')

print()
print(f'总章节数: {len(chapters)}')
