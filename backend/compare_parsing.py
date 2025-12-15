#!/usr/bin/env python3
"""
精确对比: 为什么同一个PDF文件的目录解析会不同
"""

import sys
sys.path.insert(0, '/app')

from engines.parse_engine import ParseEngine
from engines.parse_engine_v2 import EnhancedChapterExtractor

print("=" * 80)
print("精确诊断: 同一文件目录解析差异")
print("=" * 80)
print()

# 两个文件路径
file1 = '/app/./uploads/temp/b46e72a8/6f6f42e5-2689-42bc-8bad-32cedf4948cd.pdf'
file2 = '/app/./uploads/temp/fd7ccef2/6f6f42e5-2689-42bc-8bad-32cedf4948cd.pdf'

print(f"文件1: {file1}")
print(f"文件2: {file2}")
print()

# 创建解析器
parser = ParseEngine()
extractor = EnhancedChapterExtractor()

# 解析文件1
print("【文件1解析】")
print("-" * 80)

try:
    content1 = parser._parse_pdf(file1)
    print(f"✓ 提取文本长度: {len(content1)} 字符")
    
    chapters1 = extractor.extract_chapters(content1)
    print(f"✓ 提取章节数: {len(chapters1)}")
    
    # 显示前15个章节
    print("\n前15个章节:")
    for i, ch in enumerate(chapters1[:15]):
        level_marker = "  " * (ch['chapter_level'] - 1)
        print(f"  {i+1:2d}. {level_marker}[L{ch['chapter_level']}] {ch['chapter_number']} - {ch['chapter_title'][:40]}")
    
    # 提取"第二部分"及其子章节
    part2_found = False
    part2_index = -1
    for i, ch in enumerate(chapters1):
        if '第二部分' in ch['chapter_number']:
            part2_found = True
            part2_index = i
            print(f"\n✓ 找到'第二部分': 索引={i}, 标题={ch['chapter_title']}")
            break
    
    if part2_found:
        # 显示第二部分后的10个章节
        print("\n第二部分后的10个章节:")
        for i in range(part2_index + 1, min(part2_index + 11, len(chapters1))):
            ch = chapters1[i]
            level_marker = "  " * (ch['chapter_level'] - 1)
            print(f"  {i+1:2d}. {level_marker}[L{ch['chapter_level']}] {ch['chapter_number']} - {ch['chapter_title'][:40]}")
    else:
        print("\n❌ 未找到'第二部分'")
    
    print()
    
except Exception as e:
    print(f"❌ 文件1解析失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# 解析文件2
print("【文件2解析】")
print("-" * 80)

try:
    content2 = parser._parse_pdf(file2)
    print(f"✓ 提取文本长度: {len(content2)} 字符")
    
    chapters2 = extractor.extract_chapters(content2)
    print(f"✓ 提取章节数: {len(chapters2)}")
    
    # 显示前15个章节
    print("\n前15个章节:")
    for i, ch in enumerate(chapters2[:15]):
        level_marker = "  " * (ch['chapter_level'] - 1)
        print(f"  {i+1:2d}. {level_marker}[L{ch['chapter_level']}] {ch['chapter_number']} - {ch['chapter_title'][:40]}")
    
    # 提取"第二部分"及其子章节
    part2_found = False
    part2_index = -1
    for i, ch in enumerate(chapters2):
        if '第二部分' in ch['chapter_number']:
            part2_found = True
            part2_index = i
            print(f"\n✓ 找到'第二部分': 索引={i}, 标题={ch['chapter_title']}")
            break
    
    if part2_found:
        # 显示第二部分后的10个章节
        print("\n第二部分后的10个章节:")
        for i in range(part2_index + 1, min(part2_index + 11, len(chapters2))):
            ch = chapters2[i]
            level_marker = "  " * (ch['chapter_level'] - 1)
            print(f"  {i+1:2d}. {level_marker}[L{ch['chapter_level']}] {ch['chapter_number']} - {ch['chapter_title'][:40]}")
    else:
        print("\n❌ 未找到'第二部分'")
    
    print()
    
except Exception as e:
    print(f"❌ 文件2解析失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# 对比分析
print("【对比分析】")
print("-" * 80)

try:
    # 1. 文本内容对比
    print("1. 文本内容对比:")
    print(f"   文件1文本长度: {len(content1)}")
    print(f"   文件2文本长度: {len(content2)}")
    
    if content1 == content2:
        print("   ✓ 两个文件提取的文本完全相同")
    else:
        print("   ❌ 两个文件提取的文本不同！")
        
        # 找出第一个不同的位置
        for i, (c1, c2) in enumerate(zip(content1, content2)):
            if c1 != c2:
                print(f"   第一个不同位置: 字符{i}")
                print(f"   文件1: ...{content1[max(0,i-20):i+20]}...")
                print(f"   文件2: ...{content2[max(0,i-20):i+20]}...")
                break
    print()
    
    # 2. 章节数量对比
    print("2. 章节数量对比:")
    print(f"   文件1: {len(chapters1)} 个章节")
    print(f"   文件2: {len(chapters2)} 个章节")
    
    if len(chapters1) == len(chapters2):
        print("   ✓ 章节数量相同")
    else:
        print(f"   ❌ 章节数量不同，差异: {abs(len(chapters1) - len(chapters2))} 个")
    print()
    
    # 3. 章节编号对比
    print("3. 章节编号对比:")
    
    numbers1 = set(ch['chapter_number'] for ch in chapters1)
    numbers2 = set(ch['chapter_number'] for ch in chapters2)
    
    only_in_1 = numbers1 - numbers2
    only_in_2 = numbers2 - numbers1
    
    if only_in_1:
        print(f"   仅在文件1中: {sorted(only_in_1)[:10]}")
    
    if only_in_2:
        print(f"   仅在文件2中: {sorted(only_in_2)[:10]}")
    
    if not only_in_1 and not only_in_2:
        print("   ✓ 章节编号完全一致")
    print()
    
    # 4. 逐个对比章节
    print("4. 逐个对比前10个章节:")
    for i in range(min(10, len(chapters1), len(chapters2))):
        ch1 = chapters1[i]
        ch2 = chapters2[i]
        
        if ch1['chapter_number'] == ch2['chapter_number'] and ch1['chapter_title'] == ch2['chapter_title']:
            print(f"   {i+1:2d}. ✓ {ch1['chapter_number']} - {ch1['chapter_title'][:30]}")
        else:
            print(f"   {i+1:2d}. ❌ 不同!")
            print(f"       文件1: {ch1['chapter_number']} - {ch1['chapter_title'][:30]}")
            print(f"       文件2: {ch2['chapter_number']} - {ch2['chapter_title'][:30]}")
    print()
    
except Exception as e:
    print(f"❌ 对比分析失败: {e}")
    import traceback
    traceback.print_exc()

# 总结
print("=" * 80)
print("总结")
print("=" * 80)
print()
print("如果文本内容相同但章节不同，可能是:")
print("  1. EnhancedChapterExtractor内部状态问题")
print("  2. 正则表达式的非确定性匹配")
print("  3. 顺序依赖的逻辑bug (如 in_main_chapters 状态)")
print()
print("如果文本内容就不同，可能是:")
print("  1. PDF解析器使用了不同的方法")
print("  2. OCR结果不一致")
print("  3. 文件实际上不同（虽然名字相同）")
print()
