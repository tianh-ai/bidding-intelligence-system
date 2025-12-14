#!/usr/bin/env python3
"""
使用改进版解析引擎测试实际PDF文档
"""

import sys
sys.path.insert(0, '/app')

from engines.parse_engine import ParseEngine
from engines.parse_engine_v2 import EnhancedChapterExtractor

# 解析PDF
pdf_path = "/app/./uploads/temp/b46e72a8/6f6f42e5-2689-42bc-8bad-32cedf4948cd.pdf"

parser = ParseEngine()
content = parser._parse_pdf(pdf_path)

print("=" * 100)
print("使用改进版提取器解析PDF")
print("=" * 100)
print()

# 使用新提取器
extractor = EnhancedChapterExtractor()
chapters = extractor.extract_chapters(content)

print(f"总章节数: {len(chapters)}")
print()

# 统计各层级数量
level_counts = {}
for ch in chapters:
    level = ch['chapter_level']
    level_counts[level] = level_counts.get(level, 0) + 1

print("层级分布:")
for level in sorted(level_counts.keys()):
    print(f"  第{level}层: {level_counts[level]} 个")
print()

# 显示前50个章节
print("前50个章节:")
print("-" * 100)
for i, ch in enumerate(chapters[:50], 1):
    level = ch['chapter_level']
    number = ch['chapter_number']
    title = ch['chapter_title']
    indent = "  " * (level - 1)
    print(f"{i:3d}. [L{level}] {indent}{number} {title}")

print()
print("=" * 100)

# 对比旧版
print()
print("【对比】使用旧版提取器")
print("-" * 100)
old_chapters = parser._extract_from_content(content)
print(f"旧版总数: {len(old_chapters)}")
print(f"新版总数: {len(chapters)}")
print()

# 分析新增的章节
new_numbers = {ch['chapter_number'] for ch in chapters}
old_numbers = {ch.get('chapter_number', '') for ch in old_chapters}

added = new_numbers - old_numbers
print(f"新增章节: {len(added)} 个")
if added:
    for num in sorted(list(added)[:20]):
        ch = next((c for c in chapters if c['chapter_number'] == num), None)
        if ch:
            print(f"  + {ch['chapter_number']} {ch['chapter_title']}")
