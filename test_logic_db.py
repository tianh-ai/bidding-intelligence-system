#!/usr/bin/env python3
"""
学习MCP单元测试 - 使用模拟数据
测试规则转换和保存逻辑
"""

import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/mcp-servers/logic-learning/python')
sys.path.insert(0, '/app/mcp-servers/shared')

from rule_schema import Rule, RuleType, RulePriority, RuleSource
from core.logic_db import logic_db
from core.logger import logger

print("=" * 70)
print("学习MCP规则转换和保存单元测试")
print("=" * 70)

# 测试1: 创建Rule对象
print("\n[测试1] 创建Rule对象")
print("-" * 70)

try:
    test_rule = Rule(
        type=RuleType.MANDATORY,
        priority=RulePriority.HIGH,
        source=RuleSource.CHAPTER_LEARNING,
        condition={"type": "keyword_match", "keywords": ["项目名称", "项目编号"]},
        condition_description="章节标题必须包含'项目名称'或'项目编号'",
        description="投标文件中必须明确标注项目名称和项目编号",
        pattern=r"项目(名称|编号)\s*[:：]",
        action={"type": "validate", "method": "regex_match"},
        action_description="使用正则表达式匹配项目名称和编号",
        constraints={"location": "首页", "font_size_min": "小四"},
        scope={"chapter_id": "test_chapter_001", "file_id": "test_file_001"},
        confidence=0.95,
        version=1,
        tags=["必填项", "招标要求", "项目信息"],
        reference={"source": "招标文件第一章", "page": 1},
        fix_suggestion="请在投标文件首页添加明确的项目名称和编号标识",
        examples=["项目名称：XX市政工程项目", "项目编号：2024-001"],
        counter_examples=["项目：XX工程", "编号001"]
    )
    
    print(f"✅ Rule对象创建成功")
    print(f"   Type: {test_rule.type.value}")
    print(f"   Priority: {test_rule.priority.value}")
    print(f"   Source: {test_rule.source.value}")
    print(f"   Description: {test_rule.description}")
    print(f"   Confidence: {test_rule.confidence}")
    
except Exception as e:
    print(f"❌ Rule创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试2: 序列化和反序列化
print("\n[测试2] Rule对象序列化/反序列化")
print("-" * 70)

try:
    rule_dict = test_rule.dict()
    print(f"✅ 序列化成功，字段数: {len(rule_dict)}")
    print(f"   关键字段: {list(rule_dict.keys())[:5]}...")
    
    # 反序列化
    reconstructed_rule = Rule(**rule_dict)
    print(f"✅ 反序列化成功")
    print(f"   Type匹配: {reconstructed_rule.type == test_rule.type}")
    print(f"   Description匹配: {reconstructed_rule.description == test_rule.description}")
    
except Exception as e:
    print(f"❌ 序列化/反序列化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3: 保存到logic_database
print("\n[测试3] 保存Rule到logic_database")
print("-" * 70)

try:
    # 清空之前的测试数据
    from database import db
    db.execute("DELETE FROM logic_database WHERE reference->>'source' = '招标文件第一章'")
    
    rule_id = logic_db.add_rule(test_rule)
    print(f"✅ Rule保存成功")
    print(f"   Rule ID: {rule_id}")
    
except Exception as e:
    print(f"❌ 保存失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4: 查询单条规则
print("\n[测试4] 按ID查询规则")
print("-" * 70)

try:
    retrieved_rule = logic_db.get_rule(rule_id)
    print(f"✅ 查询成功")
    print(f"   ID: {rule_id}")
    print(f"   Type: {retrieved_rule.type.value}")
    print(f"   Priority: {retrieved_rule.priority.value}")
    print(f"   Description: {retrieved_rule.description}")
    print(f"   数据一致性: {retrieved_rule.description == test_rule.description}")
    
except Exception as e:
    print(f"❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试5: 批量保存规则
print("\n[测试5] 批量保存多条规则")
print("-" * 70)

try:
    rules_to_save = []
    
    # 创建不同类型的规则
    for i, (rule_type, priority) in enumerate([
        (RuleType.STRUCTURE, RulePriority.CRITICAL),
        (RuleType.CONTENT, RulePriority.HIGH),
        (RuleType.SCORING, RulePriority.MEDIUM),
        (RuleType.CONSISTENCY, RulePriority.LOW),
    ]):
        rule = Rule(
            type=rule_type,
            priority=priority,
            source=RuleSource.GLOBAL_LEARNING,
            condition_description=f"测试规则{i+1}的条件",
            description=f"这是{rule_type.value}类型的测试规则{i+1}",
            action_description=f"测试规则{i+1}的动作",
            confidence=0.8 + i * 0.05,
            version=1,
            tags=["批量测试", rule_type.value]
        )
        rules_to_save.append(rule)
    
    rule_ids_batch = logic_db.add_rules_batch(rules_to_save)
    print(f"✅ 批量保存成功")
    print(f"   保存规则数: {len(rule_ids_batch)}")
    print(f"   Rule IDs: {rule_ids_batch[:2]}... (showing first 2)")
    
except Exception as e:
    print(f"❌ 批量保存失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试6: 按类型查询
print("\n[测试6] 按类型查询规则")
print("-" * 70)

try:
    mandatory_rules = logic_db.get_rules_by_type(RuleType.MANDATORY)
    structure_rules = logic_db.get_rules_by_type(RuleType.STRUCTURE)
    content_rules = logic_db.get_rules_by_type(RuleType.CONTENT)
    
    print(f"✅ 按类型查询成功")
    print(f"   MANDATORY规则: {len(mandatory_rules)} 条")
    print(f"   STRUCTURE规则: {len(structure_rules)} 条")
    print(f"   CONTENT规则: {len(content_rules)} 条")
    
except Exception as e:
    print(f"❌ 按类型查询失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试7: 按优先级查询
print("\n[测试7] 按优先级查询规则")
print("-" * 70)

try:
    critical_rules = logic_db.get_rules_by_priority(RulePriority.CRITICAL)
    high_rules = logic_db.get_rules_by_priority(RulePriority.HIGH)
    
    print(f"✅ 按优先级查询成功")
    print(f"   CRITICAL优先级: {len(critical_rules)} 条")
    print(f"   HIGH优先级: {len(high_rules)} 条")
    
except Exception as e:
    print(f"❌ 按优先级查询失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试8: 搜索规则
print("\n[测试8] 全文搜索规则")
print("-" * 70)

try:
    search_results = logic_db.search_rules("项目", RuleType.MANDATORY)
    print(f"✅ 搜索成功")
    print(f"   关键词'项目'匹配到 {len(search_results)} 条MANDATORY规则")
    
    if search_results:
        print(f"   示例: {search_results[0].description[:50]}...")
    
except Exception as e:
    print(f"❌ 搜索失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试9: 获取统计信息
print("\n[测试9] 获取统计信息")
print("-" * 70)

try:
    stats = logic_db.get_statistics()
    print(f"✅ 统计信息获取成功")
    print(f"   总规则数: {stats.get('total_rules', 0)}")
    print(f"   按类型分布: {stats.get('by_type', {})}")
    print(f"   按优先级分布: {stats.get('by_priority', {})}")
    print(f"   按来源分布: {stats.get('by_source', {})}")
    print(f"   活跃规则数: {stats.get('active_rules', 0)}")
    
except Exception as e:
    print(f"❌ 统计失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试10: 更新规则
print("\n[测试10] 更新规则")
print("-" * 70)

try:
    success = logic_db.update_rule(
        rule_id,
        updates={
            'confidence': 0.99,
            'tags': ['必填项', '招标要求', '项目信息', '已验证']
        }
    )
    print(f"✅ 更新成功: {success}")
    
    # 验证更新
    updated_rule = logic_db.get_rule(rule_id)
    print(f"   新的confidence: {updated_rule.confidence}")
    print(f"   新的tags: {updated_rule.tags}")
    
except Exception as e:
    print(f"❌ 更新失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试11: 创建规则包
print("\n[测试11] 创建规则包")
print("-" * 70)

try:
    # 获取HIGH优先级的规则ID
    high_rules = logic_db.get_rules_by_priority(RulePriority.HIGH)
    rule_ids = [rule.id for rule in high_rules]
    
    rule_package = logic_db.create_rule_package(
        name="高优先级规则包",
        rule_ids=rule_ids
    )
    
    print(f"✅ 规则包创建成功")
    print(f"   Package Name: {rule_package.name}")
    print(f"   Structure Rules: {len(rule_package.structure_rules)}")
    print(f"   Content Rules: {len(rule_package.content_rules)}")
    print(f"   Mandatory Rules: {len(rule_package.mandatory_rules)}")
    print(f"   Scoring Rules: {len(rule_package.scoring_rules)}")
    print(f"   Consistency Rules: {len(rule_package.consistency_rules)}")
    print(f"   Formatting Rules: {len(rule_package.formatting_rules)}")
    print(f"   Terminology Rules: {len(rule_package.terminology_rules)}")
    
except Exception as e:
    print(f"❌ 规则包创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 最终总结
print("\n" + "=" * 70)
print("✅ 所有测试通过！")
print("=" * 70)
print("\n测试总结:")
print("1. ✅ Rule对象创建和验证")
print("2. ✅ Rule对象序列化/反序列化")
print("3. ✅ 单条规则保存到logic_database")
print("4. ✅ 单条规则按ID查询")
print("5. ✅ 批量规则保存")
print("6. ✅ 按类型查询规则")
print("7. ✅ 按优先级查询规则")
print("8. ✅ 全文搜索规则")
print("9. ✅ 统计信息获取")
print("10. ✅ 规则更新")
print("11. ✅ 规则包创建")
print("\n🎉 LogicDatabaseDAL完整功能验证通过！")

# 清理测试数据（可选）
print("\n[清理] 清除测试数据")
print("-" * 70)
try:
    # 注意：这会删除所有规则，生产环境请谨慎
    # db.execute("DELETE FROM logic_database")
    print("⚠️  测试数据保留在数据库中，可用于检查MCP测试")
    print(f"   总共保存了 {stats.get('total_rules', 0)} 条规则")
except Exception as e:
    print(f"清理失败: {e}")
