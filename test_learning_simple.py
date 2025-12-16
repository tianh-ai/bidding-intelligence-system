#!/usr/bin/env python3
"""
简化的学习MCP测试 - 在Docker容器内运行
"""

import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/mcp-servers/logic-learning/python')
sys.path.insert(0, '/app/mcp-servers/shared')

print("=" * 60)
print("测试 1: 导入模块")
print("=" * 60)

try:
    from database import db
    print("✅ database.db 导入成功")
except Exception as e:
    print(f"❌ database导入失败: {e}")
    sys.exit(1)

try:
    from core.logger import logger
    print("✅ logger 导入成功")
except Exception as e:
    print(f"❌ logger导入失败: {e}")
    sys.exit(1)

try:
    from core.kb_client import get_kb_client
    print("✅ kb_client 导入成功")
except Exception as e:
    print(f"❌ kb_client导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from core.logic_db import logic_db
    print("✅ logic_db 导入成功")
except Exception as e:
    print(f"❌ logic_db导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from rule_schema import Rule, RuleType, RulePriority, RuleSource
    print("✅ rule_schema 导入成功")
except Exception as e:
    print(f"❌ rule_schema导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from logic_learning import LogicLearningMCP
    print("✅ LogicLearningMCP 导入成功")
except Exception as e:
    print(f"❌ LogicLearningMCP导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试 2: 初始化MCP")
print("=" * 60)

try:
    mcp = LogicLearningMCP()
    print("✅ MCP 初始化成功")
    print(f"   - DB: {type(mcp.db)}")
    print(f"   - KB: {type(mcp.kb)}")
    print(f"   - Logic DB: {type(mcp.logic_db)}")
except Exception as e:
    print(f"❌ MCP初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试 3: 查询数据库中的文件和章节")
print("=" * 60)

try:
    # 查询文件
    files = db.query(
        "SELECT id, filename FROM uploaded_files ORDER BY created_at DESC LIMIT 3"
    )
    print(f"✅ 找到 {len(files)} 个文件:")
    for f in files:
        print(f"   - {f['filename']} ({f['id']})")
    
    if not files:
        print("⚠️  没有上传的文件，无法继续测试")
        sys.exit(0)
    
    file_id = files[0]['id']
    
    # 查询章节
    chapters = db.query(
        "SELECT id, chapter_title FROM chapters WHERE file_id = %s LIMIT 3",
        (file_id,)
    )
    print(f"\n✅ 文件 {files[0]['filename']} 有 {len(chapters)} 个章节:")
    for c in chapters:
        print(f"   - {c['chapter_title']} ({c['id']})")
    
    if not chapters:
        print("⚠️  文件没有章节，无法继续测试")
        sys.exit(0)
    
    chapter_id = chapters[0]['id']
    
except Exception as e:
    print(f"❌ 数据库查询失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试 4: 使用KB客户端获取章节")
print("=" * 60)

try:
    chapter_data = mcp._run_async(mcp.kb.get_chapter(chapter_id))
    print(f"✅ KB获取章节成功:")
    print(f"   - ID: {chapter_data.id}")
    print(f"   - 标题: {chapter_data.chapter_title}")
    print(f"   - 层级: {chapter_data.chapter_level}")
    print(f"   - 内容长度: {len(chapter_data.content) if chapter_data.content else 0} 字符")
except Exception as e:
    print(f"❌ KB获取失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试 5: 调用章节学习引擎")
print("=" * 60)

try:
    tender_chapter = {
        'id': chapter_data.id,
        'chapter_title': chapter_data.chapter_title,
        'content': chapter_data.content,
        'level': chapter_data.chapter_level,
        'order_index': chapter_data.position_order
    }
    
    chapter_package = mcp.chapter_engine.learn_chapter(
        tender_chapter=tender_chapter,
        proposal_chapter=tender_chapter,
        boq=None,
        custom_rules=None
    )
    
    print(f"✅ 引擎学习成功:")
    print(f"   - Structure Rules: {len(chapter_package.get('structure_rules', []))}")
    print(f"   - Content Rules: {len(chapter_package.get('content_rules', []))}")
    print(f"   - Mandatory Rules: {len(chapter_package.get('mandatory_rules', []))}")
    print(f"   - Scoring Rules: {len(chapter_package.get('scoring_rules', []))}")
    
    total_rules = sum(len(chapter_package.get(k, [])) for k in [
        'structure_rules', 'content_rules', 'mandatory_rules', 'scoring_rules'
    ])
    print(f"   - 总规则数: {total_rules}")
    
except Exception as e:
    print(f"❌ 引擎学习失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试 6: 转换规则为统一格式")
print("=" * 60)

try:
    unified_rules = []
    
    for rule_type_key, rule_type_enum in [
        ('structure_rules', RuleType.STRUCTURE),
        ('content_rules', RuleType.CONTENT),
        ('mandatory_rules', RuleType.MANDATORY),
        ('scoring_rules', RuleType.SCORING)
    ]:
        engine_rules = chapter_package.get(rule_type_key, [])
        if engine_rules:
            # 只转换第一条作为示例
            engine_rule = engine_rules[0]
            unified_rule = mcp._convert_engine_rule_to_unified_rule(
                engine_rule=engine_rule,
                rule_type=rule_type_enum,
                chapter_id=chapter_id
            )
            unified_rules.append(unified_rule)
            
            print(f"✅ 转换 {rule_type_key} 成功:")
            print(f"   - Type: {unified_rule.type.value}")
            print(f"   - Priority: {unified_rule.priority.value}")
            print(f"   - Source: {unified_rule.source.value}")
            print(f"   - Description: {unified_rule.description[:60]}...")
            print(f"   - Confidence: {unified_rule.confidence}")
    
    print(f"\n✅ 共转换 {len(unified_rules)} 条规则")
    
except Exception as e:
    print(f"❌ 规则转换失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试 7: 保存规则到logic_database")
print("=" * 60)

try:
    rule_ids = []
    for rule in unified_rules:
        rule_id = mcp.logic_db.add_rule(rule)
        rule_ids.append(rule_id)
        print(f"✅ 规则保存成功: {rule_id}")
        print(f"   - Type: {rule.type.value}")
        print(f"   - Description: {rule.description[:50]}...")
    
    print(f"\n✅ 共保存 {len(rule_ids)} 条规则到logic_database")
    
except Exception as e:
    print(f"❌ 规则保存失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试 8: 查询logic_database")
print("=" * 60)

try:
    # 查询统计
    stats = mcp.logic_db.get_statistics()
    print(f"✅ 数据库统计:")
    print(f"   - 总规则数: {stats.get('total_rules', 0)}")
    print(f"   - 按类型: {stats.get('by_type', {})}")
    print(f"   - 按优先级: {stats.get('by_priority', {})}")
    
    # 查询单条
    if rule_ids:
        rule = mcp.logic_db.get_rule(rule_ids[0])
        print(f"\n✅ 按ID查询成功:")
        print(f"   - ID: {rule_ids[0]}")
        print(f"   - Type: {rule.type.value}")
        print(f"   - Description: {rule.description[:50]}...")
    
    # 按类型查询
    structure_rules = mcp.logic_db.get_rules_by_type(RuleType.STRUCTURE)
    print(f"\n✅ 按类型查询 (STRUCTURE): {len(structure_rules)} 条")
    
except Exception as e:
    print(f"❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 所有测试通过！")
print("=" * 60)
print("\n📊 测试总结:")
print("1. ✅ 所有模块导入成功")
print("2. ✅ MCP初始化成功")
print("3. ✅ 数据库查询成功")
print("4. ✅ KB客户端工作正常")
print("5. ✅ 引擎学习功能正常")
print("6. ✅ 规则转换功能正常")
print("7. ✅ 规则保存到logic_database成功")
print("8. ✅ logic_database查询功能正常")
print("\n🎉 学习MCP完整工作流验证通过！")
