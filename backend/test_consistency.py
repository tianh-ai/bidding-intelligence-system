#!/usr/bin/env python3
"""
测试同一个文件多次解析是否一致
"""

import sys
sys.path.insert(0, '/app')

from engines.parse_engine_v2 import EnhancedChapterExtractor

# 创建测试文本（模拟PDF提取的内容）
test_content = """
第一部分 合同协议书

一、工程概况
二、合同工期
三、质量标准

第二部分 通用合同条款

1. 一般约定
1.1 词语定义与解释
1.1.1 合同
1.1.1.1 合同

2. 发包人
2.1 许可或批准
2.2 发包人代表

3. 承包人
3.1 承包人的一般义务
3.2 项目经理

第三部分 专用合同条款
"""

print("=" * 80)
print("测试：同一内容多次解析是否一致")
print("=" * 80)
print()

# 解析10次，看结果是否一致
results = []
for i in range(10):
    extractor = EnhancedChapterExtractor()  # 每次创建新实例
    chapters = extractor.extract_chapters(test_content)
    
    # 转换为可比较的格式
    chapter_str = "|".join([f"{ch['chapter_number']}:{ch['chapter_title']}" for ch in chapters])
    results.append(chapter_str)
    
    print(f"第{i+1}次解析: {len(chapters)} 个章节")

# 检查是否所有结果都一致
all_same = all(r == results[0] for r in results)

print()
if all_same:
    print("✓ 所有解析结果完全一致")
    print()
    print("解析结果:")
    extractor = EnhancedChapterExtractor()
    chapters = extractor.extract_chapters(test_content)
    for i, ch in enumerate(chapters):
        print(f"  {i+1:2d}. [L{ch['chapter_level']}] {ch['chapter_number']:15s} {ch['chapter_title']}")
else:
    print("❌ 解析结果不一致！")
    print()
    for i, r in enumerate(results):
        print(f"第{i+1}次: {r}")
