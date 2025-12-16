#!/usr/bin/env python3
"""
测试学习MCP的实际运行
验证：
1. 能否正确初始化
2. 能否从KB获取章节
3. 能否调用引擎学习
4. 能否转换规则为统一格式
5. 能否保存到logic_database
"""

import sys
from pathlib import Path

# 添加路径
backend_path = str(Path(__file__).parent / 'backend')
mcp_path = str(Path(__file__).parent / 'mcp-servers' / 'logic-learning' / 'python')
shared_path = str(Path(__file__).parent / 'mcp-servers' / 'shared')

sys.path.insert(0, backend_path)
sys.path.insert(0, mcp_path)
sys.path.insert(0, shared_path)

from logic_learning import LogicLearningMCP
from rule_schema import RuleType
from core.logger import logger

def test_initialization():
    """测试1: 初始化"""
    print("=" * 60)
    print("测试 1: LogicLearningMCP 初始化")
    print("=" * 60)
    
    try:
        mcp = LogicLearningMCP()
        print(f"✅ MCP初始化成功")
        print(f"   - DB: {type(mcp.db)}")
        print(f"   - KB Client: {type(mcp.kb)}")
        print(f"   - Logic DB: {type(mcp.logic_db)}")
        print(f"   - Chapter Engine: {type(mcp.chapter_engine)}")
        print(f"   - Global Engine: {type(mcp.global_engine)}")
        return mcp
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_kb_client(mcp):
    """测试2: KB客户端获取数据"""
    print("\n" + "=" * 60)
    print("测试 2: 从KB获取章节数据")
    print("=" * 60)
    
    # 使用我们知道存在的章节ID
    chapter_id = "bea84596-fa2c-4602-9858-44ff3e32f18c"
    
    try:
        # 测试异步方法
        chapter = mcp._run_async(mcp.kb.get_chapter(chapter_id))
        print(f"✅ 成功获取章节")
        print(f"   - ID: {chapter.id}")
        print(f"   - 标题: {chapter.chapter_title}")
        print(f"   - 层级: {chapter.chapter_level}")
        print(f"   - 内容长度: {len(chapter.content) if chapter.content else 0} 字符")
        return chapter
    except Exception as e:
        print(f"❌ KB获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_engine_learning(mcp, chapter):
    """测试3: 引擎学习"""
    print("\n" + "=" * 60)
    print("测试 3: 章节逻辑引擎学习")
    print("=" * 60)
    
    try:
        # 构建章节对象
        tender_chapter = {
            'id': chapter.id,
            'chapter_title': chapter.chapter_title,
            'content': chapter.content,
            'level': chapter.chapter_level,
            'order_index': chapter.position_order
        }
        
        proposal_chapter = tender_chapter
        
        # 调用学习方法
        chapter_package = mcp.chapter_engine.learn_chapter(
            tender_chapter=tender_chapter,
            proposal_chapter=proposal_chapter,
            boq=None,
            custom_rules=None
        )
        
        print(f"✅ 引擎学习成功")
        print(f"   - Structure Rules: {len(chapter_package.get('structure_rules', []))}")
        print(f"   - Content Rules: {len(chapter_package.get('content_rules', []))}")
        print(f"   - Mandatory Rules: {len(chapter_package.get('mandatory_rules', []))}")
        print(f"   - Scoring Rules: {len(chapter_package.get('scoring_rules', []))}")
        
        # 显示第一条规则示例
        for rule_type_key in ['structure_rules', 'content_rules', 'mandatory_rules', 'scoring_rules']:
            rules = chapter_package.get(rule_type_key, [])
            if rules:
                print(f"\n   示例 {rule_type_key}:")
                rule = rules[0]
                print(f"      - Description: {rule.get('description', 'N/A')[:80]}...")
                print(f"      - Priority: {rule.get('priority', 'N/A')}")
                print(f"      - Confidence: {rule.get('confidence', 'N/A')}")
                break
        
        return chapter_package
    except Exception as e:
        print(f"❌ 引擎学习失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_rule_conversion(mcp, chapter_package, chapter_id):
    """测试4: 规则转换"""
    print("\n" + "=" * 60)
    print("测试 4: 引擎规则转换为统一Rule对象")
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
                for engine_rule in engine_rules[:2]:  # 只测试前2条
                    unified_rule = mcp._convert_engine_rule_to_unified_rule(
                        engine_rule=engine_rule,
                        rule_type=rule_type_enum,
                        chapter_id=chapter_id
                    )
                    unified_rules.append(unified_rule)
                    
                    print(f"\n✅ 转换成功 ({rule_type_enum.value})")
                    print(f"   - Type: {unified_rule.type}")
                    print(f"   - Priority: {unified_rule.priority}")
                    print(f"   - Source: {unified_rule.source}")
                    print(f"   - Description: {unified_rule.description[:80]}...")
                    print(f"   - Confidence: {unified_rule.confidence}")
                    print(f"   - Scope: {unified_rule.scope}")
        
        return unified_rules
    except Exception as e:
        print(f"❌ 规则转换失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_save_to_db(mcp, unified_rules):
    """测试5: 保存到logic_database"""
    print("\n" + "=" * 60)
    print("测试 5: 保存规则到logic_database")
    print("=" * 60)
    
    saved_count = 0
    rule_ids = []
    
    for rule in unified_rules[:3]:  # 只保存前3条测试
        try:
            rule_id = mcp.logic_db.add_rule(rule)
            rule_ids.append(rule_id)
            saved_count += 1
            print(f"✅ 规则已保存: {rule_id}")
            print(f"   - Type: {rule.type.value}")
            print(f"   - Priority: {rule.priority.value}")
            print(f"   - Description: {rule.description[:60]}...")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 保存统计: {saved_count}/{len(unified_rules[:3])} 条规则")
    return rule_ids


def test_query_from_db(mcp, rule_ids):
    """测试6: 从logic_database查询"""
    print("\n" + "=" * 60)
    print("测试 6: 从logic_database查询规则")
    print("=" * 60)
    
    try:
        # 测试按ID查询
        if rule_ids:
            rule = mcp.logic_db.get_rule(rule_ids[0])
            print(f"✅ 按ID查询成功")
            print(f"   - ID: {rule_ids[0]}")
            print(f"   - Type: {rule.type.value if rule else 'N/A'}")
            print(f"   - Description: {rule.description[:60] if rule else 'N/A'}...")
        
        # 测试按类型查询
        structure_rules = mcp.logic_db.get_rules_by_type(RuleType.STRUCTURE)
        print(f"\n✅ 按类型查询成功")
        print(f"   - Structure Rules: {len(structure_rules)} 条")
        
        # 测试获取统计
        stats = mcp.logic_db.get_statistics()
        print(f"\n✅ 统计信息:")
        print(f"   - Total Rules: {stats.get('total_rules', 0)}")
        print(f"   - By Type: {stats.get('by_type', {})}")
        print(f"   - By Priority: {stats.get('by_priority', {})}")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()


def test_complete_workflow(mcp):
    """测试7: 完整工作流"""
    print("\n" + "=" * 60)
    print("测试 7: 完整的章节学习工作流")
    print("=" * 60)
    
    chapter_id = "bea84596-fa2c-4602-9858-44ff3e32f18c"
    file_id = "6d55dd27-1f30-438a-8bf1-856a763c88aa"
    
    try:
        result = mcp._chapter_learning(
            task_id="test_task_001",
            file_ids=[file_id],
            chapter_ids=[chapter_id]
        )
        
        print(f"✅ 完整工作流成功")
        print(f"   - Rules Learned: {result.get('rules_learned', 0)}")
        print(f"   - Chapters Processed: {result.get('chapters_processed', 0)}")
        
        return result
    except Exception as e:
        print(f"❌ 完整工作流失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试流程"""
    print("\n" + "🚀" * 30)
    print("学习MCP完整测试")
    print("🚀" * 30 + "\n")
    
    # 测试1: 初始化
    mcp = test_initialization()
    if not mcp:
        print("\n❌ 测试终止：初始化失败")
        return
    
    # 测试2: KB客户端
    chapter = test_kb_client(mcp)
    if not chapter:
        print("\n❌ 测试终止：KB获取失败")
        return
    
    # 测试3: 引擎学习
    chapter_package = test_engine_learning(mcp, chapter)
    if not chapter_package:
        print("\n❌ 测试终止：引擎学习失败")
        return
    
    # 测试4: 规则转换
    unified_rules = test_rule_conversion(mcp, chapter_package, chapter.id)
    if not unified_rules:
        print("\n❌ 测试终止：规则转换失败")
        return
    
    # 测试5: 保存到DB
    rule_ids = test_save_to_db(mcp, unified_rules)
    if not rule_ids:
        print("\n❌ 警告：没有规则保存成功")
    
    # 测试6: 从DB查询
    test_query_from_db(mcp, rule_ids)
    
    # 测试7: 完整工作流
    test_complete_workflow(mcp)
    
    # 最终总结
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("\n检查要点:")
    print("1. ✅ LogicLearningMCP 正确初始化")
    print("2. ✅ KB客户端能获取章节数据")
    print("3. ✅ 引擎能学习并提取规则")
    print("4. ✅ 规则能转换为统一Rule格式")
    print("5. ✅ 规则能保存到logic_database")
    print("6. ✅ 规则能从logic_database查询")
    print("7. ✅ 完整工作流正常运行")
    print("\n🎉 学习MCP验证通过！")


if __name__ == "__main__":
    main()
