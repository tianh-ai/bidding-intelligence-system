"""
简化系统测试 - 检查所有模块是否可导入
"""

import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("🚀 开始系统模块导入测试...\n")

tests_passed = 0
tests_total = 0

# 测试1: 本体管理系统
print("="*60)
print("测试1: 本体管理系统")
print("="*60)
tests_total += 1
try:
    from db.ontology import (
        OntologyManager, OntologyNode, OntologyRelation,
        NodeType, RelationType, OntologyPath
    )
    print("✅ 导入成功: OntologyManager, OntologyNode, OntologyRelation")
    print(f"   - 节点类型: {len(NodeType.__members__)}个")
    print(f"   - 关系类型: {len(RelationType.__members__)}个")
    tests_passed += 1
except Exception as e:
    print(f"❌ 导入失败: {e}")

# 测试2: 预处理代理
print("\n" + "="*60)
print("测试2: 预处理代理（Layer 1）")
print("="*60)
tests_total += 1
try:
    from agents.preprocessor import (
        PreprocessorAgent, TextBlock, TableBlock,
        ChapterNode, DocumentStructure
    )
    print("✅ 导入成功: PreprocessorAgent")
    
    # 测试初始化
    agent = PreprocessorAgent()
    print(f"   - 章节模式: {len(agent.chapter_patterns)}个")
    print(f"   - 关键词模式: {len(agent.keyword_patterns)}个")
    tests_passed += 1
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 约束提取代理
print("\n" + "="*60)
print("测试3: 约束提取代理（Layer 2）")
print("="*60)
tests_total += 1
try:
    from agents.constraint_extractor import (
        ConstraintExtractorAgent, ExtractedConstraint,
        ConstraintType, ConstraintCategory
    )
    print("✅ 导入成功: ConstraintExtractorAgent")
    print(f"   - 约束类型: {len(ConstraintType.__members__)}个")
    print(f"   - 约束分类: {len(ConstraintCategory.__members__)}个")
    tests_passed += 1
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 智能路由器
print("\n" + "="*60)
print("测试4: 智能路由器（85/10/5策略）")
print("="*60)
tests_total += 1
try:
    from engines.smart_router import (
        SmartRouter, RequirementNode, RoutingDecision,
        ContentSource, RoutingStats
    )
    print("✅ 导入成功: SmartRouter")
    print(f"   - 内容来源: {len(ContentSource.__members__)}个")
    tests_passed += 1
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试5: 多代理评估器
print("\n" + "="*60)
print("测试5: 多代理评估器（三层检查）")
print("="*60)
tests_total += 1
try:
    from engines.multi_agent_evaluator import (
        MultiAgentEvaluator, HardConstraintChecker,
        SoftConstraintChecker, OntologyValidator,
        EvaluationReport, CheckResult
    )
    print("✅ 导入成功: MultiAgentEvaluator")
    print("   - HardConstraintChecker: 硬约束检查器")
    print("   - SoftConstraintChecker: 软约束检查器")
    print("   - OntologyValidator: 知识图谱验证器")
    tests_passed += 1
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 汇总报告
print("\n" + "="*60)
print("📊 测试汇总报告")
print("="*60)
print(f"通过: {tests_passed}/{tests_total}")
print(f"成功率: {tests_passed/tests_total*100:.1f}%")

if tests_passed == tests_total:
    print("\n🎉 所有模块导入成功！系统就绪！")
    sys.exit(0)
else:
    print(f"\n⚠️  还有 {tests_total - tests_passed} 个模块需要修复")
    sys.exit(1)
