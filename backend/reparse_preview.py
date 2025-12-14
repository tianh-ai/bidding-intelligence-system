#!/usr/bin/env python3
"""
Re-parse target PDF with enhanced extractor and print summary.
"""

import sys
sys.path.insert(0, '/app')
from engines.parse_engine import ParseEngine
from engines.parse_engine_v2 import EnhancedChapterExtractor

PDF_PATH = '/app/./uploads/temp/b46e72a8/6f6f42e5-2689-42bc-8bad-32cedf4948cd.pdf'

def main():
    parser = ParseEngine()
    content = parser._parse_pdf(PDF_PATH)
    extractor = EnhancedChapterExtractor()
    chapters = extractor.extract_chapters(content)

    print(f'总章节数: {len(chapters)}')
    levels = {}
    for ch in chapters:
        levels[ch['chapter_level']] = levels.get(ch['chapter_level'], 0) + 1
    level_summary = ' | '.join([f"L{l}:{levels[l]}" for l in sorted(levels.keys())])
    print(f'层级分布: {level_summary}')

    main_chapters = [ch for ch in chapters if ch['chapter_level'] == 2]
    print('\n第2层主章节 (前30):')
    for i, ch in enumerate(main_chapters[:30], 1):
        print(f"{i:2d}. {ch['chapter_number']} {ch['chapter_title']}")

    print('\n前40条:')
    for i, ch in enumerate(chapters[:40], 1):
        l = ch['chapter_level']
        indent = '  ' * (l-1)
        title = ch['chapter_title'].replace('\n',' ')[:60]
        print(f"{i:3d}. [L{l}] {indent}{ch['chapter_number']} {title}")

if __name__ == '__main__':
    main()
