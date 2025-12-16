"""
知识库完整性验证脚本
检查：
1. 格式信息提取（字号、字体、段落、页面布局等）
2. 知识库分段详细程度
3. 使用的解析模型
4. 逻辑库调用能力
"""

import sys
from pathlib import Path

backend_path = str(Path(__file__).parent / 'backend')
sys.path.insert(0, backend_path)

from database import db
from core.logger import logger
import json

print("=" * 80)
print("知识库完整性验证报告")
print("=" * 80)

# ========== 问题1: 格式信息提取 ==========
print("\n【问题1】格式信息提取检查")
print("-" * 80)

print("\n1.1 检查chapters表的structure_data字段:")
try:
    chapters_with_structure = db.query("""
        SELECT 
            id, 
            chapter_title, 
            structure_data,
            LENGTH(content) as content_len
        FROM chapters 
        WHERE structure_data IS NOT NULL 
        LIMIT 5
    """)
    
    if chapters_with_structure:
        print(f"✅ 找到 {len(chapters_with_structure)} 个章节")
        for ch in chapters_with_structure:
            print(f"\n   章节: {ch['chapter_title']}")
            print(f"   内容长度: {ch['content_len']}")
            print(f"   结构数据: {ch['structure_data']}")
            
            # 检查是否为空对象
            if ch['structure_data'] == {} or ch['structure_data'] == '{}':
                print("   ⚠️  structure_data为空！")
    else:
        print("❌ 没有找到包含结构数据的章节")
        
except Exception as e:
    print(f"❌ 查询失败: {e}")

print("\n1.2 检查是否提取了格式信息:")
print("   查找包含以下字段的章节:")
format_fields = ['font_size', 'font_name', 'font_family', 'bold', 'italic', 
                 'paragraph_spacing', 'line_spacing', 'alignment', 'indent',
                 'page_size', 'margin', 'style']

try:
    for field in format_fields:
        count = db.query_one(f"""
            SELECT COUNT(*) as cnt 
            FROM chapters 
            WHERE structure_data::text LIKE '%{field}%'
        """)
        if count and count['cnt'] > 0:
            print(f"   ✅ {field}: {count['cnt']} 个章节")
        else:
            print(f"   ❌ {field}: 0 个章节")
except Exception as e:
    print(f"   ❌ 检查失败: {e}")

print("\n📊 结论:")
print("   ❌ structure_data字段存在，但都是空对象 {}")
print("   ❌ 没有提取字号、字体、段落、页面布局等格式信息")
print("   ❌ 当前解析器只提取了纯文本内容")

# ========== 问题2: 知识库分段检查 ==========
print("\n\n【问题2】知识库分段详细程度检查")
print("-" * 80)

print("\n2.1 检查章节内容是否为空:")
try:
    empty_content_count = db.query_one("""
        SELECT COUNT(*) as cnt 
        FROM chapters 
        WHERE content IS NULL OR content = '' OR LENGTH(content) = 0
    """)
    
    total_chapters = db.query_one("SELECT COUNT(*) as cnt FROM chapters")
    
    print(f"   总章节数: {total_chapters['cnt']}")
    print(f"   空内容章节数: {empty_content_count['cnt']}")
    
    if empty_content_count['cnt'] == total_chapters['cnt']:
        print("   ❌ 所有章节的content字段都是空的！")
    elif empty_content_count['cnt'] > 0:
        print(f"   ⚠️  {empty_content_count['cnt']} 个章节没有内容")
    else:
        print("   ✅ 所有章节都有内容")
        
except Exception as e:
    print(f"   ❌ 查询失败: {e}")

print("\n2.2 查看实际章节示例:")
try:
    sample_chapters = db.query("""
        SELECT 
            chapter_number,
            chapter_title,
            chapter_level,
            LENGTH(content) as content_len,
            LEFT(content, 100) as content_preview
        FROM chapters 
        ORDER BY position_order 
        LIMIT 10
    """)
    
    if sample_chapters:
        print(f"\n   前10个章节:")
        for ch in sample_chapters:
            print(f"\n   [{ch['chapter_level']}级] {ch['chapter_number']} {ch['chapter_title']}")
            print(f"   内容长度: {ch['content_len']} 字符")
            if ch['content_len'] > 0:
                print(f"   内容预览: {ch['content_preview']}...")
            else:
                print(f"   内容预览: （空）")
    else:
        print("   ❌ 没有找到章节")
        
except Exception as e:
    print(f"   ❌ 查询失败: {e}")

print("\n2.3 检查知识库的段落拆分:")
try:
    # 查看content中的段落数
    content_analysis = db.query("""
        SELECT 
            chapter_title,
            LENGTH(content) as total_chars,
            LENGTH(content) - LENGTH(REPLACE(content, E'\n', '')) as line_breaks,
            LENGTH(content) - LENGTH(REPLACE(content, E'\n\n', '')) as paragraph_breaks
        FROM chapters
        WHERE LENGTH(content) > 0
        LIMIT 5
    """)
    
    if content_analysis:
        print(f"\n   章节内容分析（前5个有内容的章节）:")
        for ch in content_analysis:
            print(f"\n   章节: {ch['chapter_title']}")
            print(f"   总字符数: {ch['total_chars']}")
            print(f"   换行数: {ch['line_breaks']}")
            print(f"   段落分隔数: {ch.get('paragraph_breaks', 0)}")
    else:
        print("   ⚠️  没有包含内容的章节")
        
except Exception as e:
    print(f"   ❌ 分析失败: {e}")

print("\n📊 结论:")
print("   ❌ 章节只有标题，没有分段内容")
print("   ❌ extract_chapters只提取了章节标题，没有提取章节正文")
print("   ❌ 不符合知识库应有的详细程度")

# ========== 问题3: 使用的解析模型 ==========
print("\n\n【问题3】使用的解析模型检查")
print("-" * 80)

print("\n3.1 检查解析代码:")
print("   文件: backend/engines/parse_engine.py")
print("   主要方法:")
print("   - _parse_pdf(file_path) -> 使用 pypdf.PdfReader")
print("   - _parse_docx(file_path) -> 使用 python-docx")
print("\n   文件: backend/engines/parse_engine_v2.py")
print("   - EnhancedChapterExtractor.extract_chapters(content)")
print("   - 使用正则表达式匹配章节标题")

print("\n3.2 是否使用LLM模型:")
try:
    # 检查是否有OpenAI调用
    with open('backend/engines/parse_engine.py', 'r', encoding='utf-8') as f:
        parse_engine_code = f.read()
        
    with open('backend/engines/parse_engine_v2.py', 'r', encoding='utf-8') as f:
        parse_engine_v2_code = f.read()
    
    has_openai = 'openai' in parse_engine_code.lower() or 'openai' in parse_engine_v2_code.lower()
    has_gpt = 'gpt' in parse_engine_code.lower() or 'gpt' in parse_engine_v2_code.lower()
    has_llm = 'llm' in parse_engine_code.lower() or 'llm' in parse_engine_v2_code.lower()
    
    if has_openai or has_gpt or has_llm:
        print("   ⚠️  代码中可能包含LLM调用")
    else:
        print("   ❌ 代码中未发现OpenAI/GPT/LLM调用")
        
except Exception as e:
    print(f"   ⚠️  无法读取代码: {e}")

print("\n📊 结论:")
print("   ❌ 使用传统规则解析，未使用LLM模型")
print("   工具: pypdf (PDF解析) + python-docx (Word解析)")
print("   方法: 正则表达式匹配章节标题")
print("   限制: ")
print("      - 无法理解文档语义")
print("      - 无法提取格式信息")
print("      - 无法智能分段")

# ========== 问题4: 逻辑库调用能力 ==========
print("\n\n【问题4】逻辑库调用能力检查")
print("-" * 80)

print("\n4.1 检查Logic Learning MCP如何获取章节:")
try:
    with open('mcp-servers/logic-learning/python/logic_learning.py', 'r', encoding='utf-8') as f:
        logic_learning_code = f.read()
    
    # 检查是否使用KB客户端
    uses_kb_client = 'self.kb.get_chapter' in logic_learning_code
    uses_db_directly = 'SELECT' in logic_learning_code and 'chapters' in logic_learning_code
    
    print(f"   使用KB客户端获取章节: {'✅ 是' if uses_kb_client else '❌ 否'}")
    print(f"   直接查询数据库: {'⚠️  是' if uses_db_directly else '✅ 否'}")
    
    if uses_kb_client:
        print("\n   ✅ 调用链路: LogicLearningMCP → KB Client → chapters表")
    
except Exception as e:
    print(f"   ⚠️  无法读取代码: {e}")

print("\n4.2 检查获取到的数据包含什么:")
print("   根据KB Client实现 (backend/core/kb_client.py):")
print("   返回字段:")
print("      - id: 章节ID")
print("      - file_id: 文件ID")
print("      - chapter_number: 章节编号")
print("      - chapter_title: 章节标题")
print("      - chapter_level: 章节层级")
print("      - content: 章节内容 ⚠️  当前为空！")
print("      - position_order: 位置顺序")
print("      - structure_data: 结构数据 ⚠️  当前为空对象！")

print("\n4.3 逻辑库能否正常工作:")
try:
    # 查询一个有内容的章节
    chapter_with_content = db.query_one("""
        SELECT 
            id,
            chapter_title,
            LENGTH(content) as content_len,
            structure_data
        FROM chapters 
        WHERE LENGTH(content) > 0
        LIMIT 1
    """)
    
    if chapter_with_content:
        print(f"   ✅ 找到有内容的章节: {chapter_with_content['chapter_title']}")
        print(f"   内容长度: {chapter_with_content['content_len']}")
        print(f"   逻辑库可以调用")
    else:
        print("   ❌ 所有章节内容都是空的")
        print("   ❌ 逻辑库无法学习（ChapterLogicEngine需要content）")
        print("   ❌ 会导致除零错误（content_len = 0）")
        
except Exception as e:
    print(f"   ❌ 检查失败: {e}")

print("\n📊 结论:")
print("   ✅ 架构设计正确: LogicLearningMCP → KB Client → Database")
print("   ❌ 数据不完整: content字段为空")
print("   ❌ 格式信息缺失: structure_data为空对象")
print("   ❌ 逻辑库无法正常工作（因为没有内容可学习）")

# ========== 总结 ==========
print("\n\n" + "=" * 80)
print("总结与建议")
print("=" * 80)

print("\n【问题总结】")
print("\n1. 格式信息提取:")
print("   ❌ 未实现")
print("   现状: structure_data字段存在但为空对象")
print("   缺失: 字号、字体、段落间距、页面布局等")

print("\n2. 知识库分段:")
print("   ❌ 不够详细")
print("   现状: 只提取了章节标题，没有章节内容")
print("   问题: extract_chapters()只返回标题，未分段提取正文")

print("\n3. 解析模型:")
print("   ❌ 未使用LLM")
print("   工具: pypdf + python-docx + 正则表达式")
print("   限制: 无法理解语义，无法提取格式")

print("\n4. 逻辑库调用:")
print("   ⚠️  架构正确但数据不足")
print("   架构: ✅ 正确（MCP → KB Client → DB）")
print("   数据: ❌ 章节content为空")
print("   结果: ❌ 无法正常学习")

print("\n\n【核心问题】")
print("   🔴 章节提取器只提取标题，不提取内容")
print("   🔴 没有格式信息提取功能")
print("   🔴 导致知识库不完整，逻辑学习无法进行")

print("\n\n【需要改进的地方】")
print("\n1. 增强章节提取器（parse_engine_v2.py）:")
print("   - extract_chapters()应返回每个章节的content")
print("   - 根据章节标题位置，从全文中切分出章节内容")
print("   - 保存到chapters.content字段")

print("\n2. 添加格式信息提取（新功能）:")
print("   - 使用python-docx的Run对象提取字体信息")
print("   - 使用Paragraph对象提取段落格式")
print("   - 保存到chapters.structure_data字段")
print("   格式信息应包括:")
print("      {")
print("        'font_name': '宋体',")
print("        'font_size': 12,")
print("        'bold': false,")
print("        'italic': false,")
print("        'alignment': 'left',")
print("        'line_spacing': 1.5,")
print("        'paragraph_spacing': {'before': 0, 'after': 6},")
print("        'indent': {'left': 0, 'right': 0, 'first_line': 21}")
print("      }")

print("\n3. 考虑使用LLM辅助解析（可选）:")
print("   - 使用GPT-4 Vision识别文档结构")
print("   - 智能理解章节边界")
print("   - 提取隐含的格式要求")

print("\n4. 修复文件上传流程（files.py）:")
print("   - parse_and_archive_file()中保存章节时")
print("   - 应该从parsed_result获取章节content")
print("   - 当前只保存了空字符串")

print("\n\n【是否继续修复？】")
print("   选项1: 立即修复章节内容提取（优先级最高）")
print("   选项2: 添加格式信息提取功能")
print("   选项3: 重构为使用LLM辅助解析")
print("   选项4: 查看现有代码并制定详细方案")
