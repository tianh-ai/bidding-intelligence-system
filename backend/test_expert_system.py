"""
专家级优化系统完整性测试
测试三层代理架构 + 本体图谱 + 智能路由 + 多代理评估
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.logger import logger
from backend.db.ontology import OntologyManager, OntologyNode, OntologyRelation, NodeType, RelationType
from backend.agents.preprocessor import PreprocessorAgent, RequirementNode
from backend.agents.constraint_extractor import ConstraintExtractorAgent
from backend.engines.smart_router import SmartRouter
from backend.engines.multi_agent_evaluator import MultiAgentEvaluator


class MockDBConnection:
    """模拟数据库连接（用于测试）"""
    
    async def fetchval(self, query, *args):
        """模拟fetchval"""
        if "INSERT INTO ontology_nodes" in query:
            from uuid import uuid4
            return uuid4()
        if "INSERT INTO ontology_relations" in query:
            from uuid import uuid4
            return uuid4()
        return None
    
    async def fetchrow(self, query, *args):
        """模拟fetchrow"""
        if "SELECT id, node_type" in query:
            return {
                'id': 'test-uuid',
                'node_type': 'requirement',
                'name': '测试节点',
                'description': '测试描述',
                'properties': {}
            }
        if "SELECT content" in query and "kb_templates" in query:
            return {
                'content': '这是知识库中的示例内容',
                'similarity': 0.85
            }
        return None
    
    async def fetch(self, query, *args):
        """模拟fetch"""
        return []
    
    async def execute(self, query, *args):
        """模拟execute"""
        return None


async def test_ontology_system():
    """测试本体知识图谱系统"""
    print("\n" + "="*60)
    print("🧪 测试1：本体知识图谱系统")
    print("="*60)
    
    db = MockDBConnection()
    ontology = OntologyManager(db)
    
    try:
        # 创建节点
        node = OntologyNode(
            node_type=NodeType.REQUIREMENT,
            name="ISO9001认证",
            description="必须具备ISO9001质量管理体系认证",
            properties={"mandatory": True}
        )
        
        node_id = await ontology.create_node(node)
        print(f"✅ 创建本体节点成功: {node_id}")
        
        # 创建关系
        evidence_node = OntologyNode(
            node_type=NodeType.EVIDENCE,
            name="ISO9001证书扫描件",
            description="有效期内的证书"
        )
        
        evidence_id = await ontology.create_node(evidence_node)
        
        relation = OntologyRelation(
            from_node_id=node_id,
            to_node_id=evidence_id,
            relation_type=RelationType.REQUIRES,
            weight=1.0
        )
        
        relation_id = await ontology.create_relation(relation)
        print(f"✅ 创建本体关系成功: {relation_id}")
        
        print("✅ 本体知识图谱系统测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 本体系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_preprocessor_agent():
    """测试预处理代理"""
    print("\n" + "="*60)
    print("🧪 测试2：预处理代理（Layer 1）")
    print("="*60)
    
    try:
        agent = PreprocessorAgent()
        print("✅ 预处理代理初始化成功")
        
        # 测试文本类型分类
        test_texts = [
            "第一章 项目概述",
            "1. 这是一个列表项",
            "这是一个普通段落文本。"
        ]
        
        for text in test_texts:
            text_type = agent._classify_text_type(text)
            print(f"  - '{text[:20]}...' → {text_type}")
        
        # 测试表格转Markdown
        headers = ["项目", "要求", "得分"]
        data = [
            ["资质证书", "ISO9001", "20分"],
            ["项目经验", "3年以上", "30分"]
        ]
        
        markdown = agent._table_to_markdown(headers, data)
        print(f"✅ 表格转Markdown成功:\n{markdown}")
        
        print("✅ 预处理代理测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 预处理代理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_constraint_extractor():
    """测试约束提取代理"""
    print("\n" + "="*60)
    print("🧪 测试3：约束提取代理（Layer 2）")
    print("="*60)
    
    db = MockDBConnection()
    ontology = OntologyManager(db)
    
    try:
        agent = ConstraintExtractorAgent(ontology)
        print("✅ 约束提取代理初始化成功")
        
        # 测试降级规则提取（不调用OpenAI）
        test_text = "投标人必须具备有效的营业执照和相关资质证书"
        
        result = await agent._fallback_rule_based_extraction(test_text, "test_block")
        print(f"✅ 规则提取成功: 发现{len(result.constraints)}个约束")
        
        for constraint in result.constraints:
            print(f"  - {constraint.title}: {constraint.constraint_type}")
        
        print("✅ 约束提取代理测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 约束提取代理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_smart_router():
    """测试智能路由器"""
    print("\n" + "="*60)
    print("🧪 测试4：智能路由器（85/10/5策略）")
    print("="*60)
    
    db = MockDBConnection()
    
    try:
        router = SmartRouter(db)
        print("✅ 智能路由器初始化成功")
        
        # 测试统计功能
        stats = router.get_stats()
        print(f"✅ 获取统计数据成功: {stats.total_requests}个请求")
        
        # 测试效率分析
        analysis = await router.analyze_routing_efficiency()
        print(f"✅ 效率分析成功:")
        print(f"  - KB匹配目标: {analysis['target_vs_actual']['kb_target']}")
        print(f"  - 实际成本: {analysis['cost_analysis']['actual_cost']}")
        
        print("✅ 智能路由器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 智能路由器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_agent_evaluator():
    """测试多代理评估器"""
    print("\n" + "="*60)
    print("🧪 测试5：多代理评估器（三层检查）")
    print("="*60)
    
    db = MockDBConnection()
    ontology = OntologyManager(db)
    
    try:
        evaluator = MultiAgentEvaluator(ontology)
        print("✅ 多代理评估器初始化成功")
        
        # 测试硬约束检查
        proposal = {
            "id": "test-proposal",
            "certifications": ["ISO9001", "ISO14001"],
            "total_price": 50000,
            "page_count": 50,
            "file_format": "PDF"
        }
        
        tender = {
            "id": "test-tender",
            "required_fields": ["company_name", "contact"],
            "required_certifications": ["ISO9001"],
            "max_budget": 100000,
            "format_requirements": {
                "max_pages": 100,
                "allowed_formats": ["PDF", "DOCX"]
            }
        }
        
        hard_results = await evaluator.hard_checker.check(proposal, tender)
        print(f"✅ 硬约束检查完成: {len(hard_results)}项检查")
        
        for result in hard_results:
            print(f"  - {result.check_name}: {result.status.value} ({result.score}分)")
        
        # 测试软约束检查（不调用LLM）
        soft_results = await evaluator.soft_checker._check_professionalism(proposal)
        print(f"✅ 软约束检查完成: {soft_results.check_name} = {soft_results.score}分")
        
        print("✅ 多代理评估器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 多代理评估器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "🚀"*30)
    print("专家级优化系统完整性测试开始")
    print("🚀"*30)
    
    tests = [
        ("本体知识图谱", test_ontology_system),
        ("预处理代理", test_preprocessor_agent),
        ("约束提取代理", test_constraint_extractor),
        ("智能路由器", test_smart_router),
        ("多代理评估器", test_multi_agent_evaluator),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试{name}出现异常: {e}")
            results.append((name, False))
    
    # 汇总报告
    print("\n" + "="*60)
    print("📊 测试汇总报告")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统就绪！")
        return 0
    else:
        print(f"\n⚠️  还有 {total - passed} 个测试需要修复")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
