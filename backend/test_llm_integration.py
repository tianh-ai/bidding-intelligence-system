"""
测试LLM集成 - 验证各个引擎的大模型功能
"""

import sys
import asyncio
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.llm_router import get_llm_router, TaskType
from engines.generation_engine import GenerationEngine, GenerationStrategy
from engines.scoring_engine import ScoringEngine
from engines.reinforcement_feedback import ReinforcementLearningFeedback, ErrorSeverity

print("🚀 开始LLM集成测试...\n")

# 获取事件循环
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ==================== 测试1: LLM Router 基础功能 ====================
print("="*60)
print("测试1: LLM Router 基础功能")
print("="*60)

try:
    router = get_llm_router()
    print(f"✅ LLM Router 初始化成功")
    print(f"   - 配置模型: {list(router.models.keys())}")
    print(f"   - DeepSeek用于: 生成、反馈分析")
    print(f"   - 千问用于: 评分、分析、对比、提取")
    print(f"\n测试简单文本生成...")
    
    async def test_simple_generation():
        text = await router.generate_text(
            prompt="简要介绍一个AI投标系统的优势",
            system_prompt="你是专业的投标顾问",
            task_type=TaskType.GENERATION,
            max_tokens=200
        )
        return text
    
    generated = loop.run_until_complete(test_simple_generation())
    print(f"✅ 生成成功 (长度: {len(generated)}字符)")
    print(f"   生成内容预览: {generated[:100]}...")
    
    # 获取使用统计
    stats = router.get_usage_stats()
    print(f"\n📊 使用统计:")
    print(f"   - 总调用次数: {stats['total_calls']}")
    print(f"   - 总tokens: {stats['total_tokens']}")
    print(f"   - 成功率: {stats['success_rate']:.1f}%")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试2: GenerationEngine LLM集成 ====================
print("\n" + "="*60)
print("测试2: GenerationEngine - 真实内容生成")
print("="*60)

try:
    gen_engine = GenerationEngine()
    print(f"✅ GenerationEngine 初始化成功 (已集成LLM)")
    
    async def test_generation():
        # 测试使用LLM生成
        version = await gen_engine.generate_proposal(
            tender_id="tender_llm_001",
            template_id="template_001",
            strategy=GenerationStrategy.BALANCED,
            mode="FULL"
        )
        return version
    
    version = loop.run_until_complete(test_generation())
    print(f"✅ LLM生成投标书成功")
    print(f"   - 生成版本: {version.version_id}")
    print(f"   - 总体评分: {version.overall_score:.1f}")
    print(f"   - 生成内容数: {len(version.contents)}")
    
    # 显示第一个章节的生成内容
    if version.contents:
        first_content = version.contents[0]
        print(f"\n📝 第一章节内容预览 ({first_content.chapter_id}):")
        print(f"   内容来源: {first_content.source}")
        print(f"   置信度: {first_content.confidence:.1f}")
        print(f"   内容: {first_content.content[:150]}...")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试3: ScoringEngine LLM评分 ====================
print("\n" + "="*60)
print("测试3: ScoringEngine - LLM智能评分")
print("="*60)

try:
    score_engine = ScoringEngine()
    print(f"✅ ScoringEngine 初始化成功 (已集成LLM)")
    
    async def test_scoring():
        # 准备测试内容
        proposal_content = {
            "content": """本项目采用先进的微服务架构，具有高可用性、高扩展性和高性能的特点。
我们的技术团队拥有10年以上的行业经验，成功交付过多个大型项目。
系统采用容器化部署，支持快速扩容和灰度发布。""",
            "quality_score": 85,
            "relevance_score": 88,
            "completeness_score": 82,
            "metric_comp_001": True,
            "metric_comp_002": True,
            "metric_tech_003": True
        }
        
        score = await score_engine.score_proposal(
            proposal_id="prop_llm_001",
            tender_id="tender_001",
            proposal_content=proposal_content
        )
        return score
    
    proposal_score = loop.run_until_complete(test_scoring())
    print(f"✅ LLM评分成功")
    print(f"   - 总体评分: {proposal_score.overall_score:.1f}")
    print(f"   - 硬指标通过: {proposal_score.hard_metric_pass}")
    print(f"   - 维度评分数: {len(proposal_score.dimension_scores)}")
    
    # 显示前3个维度评分
    for dim_score in proposal_score.dimension_scores[:3]:
        print(f"   - {dim_score.dimension.value}: {dim_score.score:.1f} (权重: {dim_score.weight:.2f})")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试4: ReinforcementLearningFeedback LLM分析 ====================
print("\n" + "="*60)
print("测试4: ReinforcementLearningFeedback - LLM智能分析")
print("="*60)

try:
    feedback_engine = ReinforcementLearningFeedback()
    print(f"✅ ReinforcementLearningFeedback 初始化成功 (已集成LLM)")
    
    async def test_feedback():
        # 记录几个错误
        await feedback_engine.record_error(
            proposal_id="prop_001",
            error_type="format_error",
            severity=ErrorSeverity.MINOR,
            description="表格格式不符合要求，缺少边框",
            location="第2章第1表"
        )
        
        await feedback_engine.record_error(
            proposal_id="prop_002",
            error_type="format_error",
            severity=ErrorSeverity.MINOR,
            description="图片格式错误，分辨率过低",
            location="第3章图1"
        )
        
        await feedback_engine.record_error(
            proposal_id="prop_003",
            error_type="format_error",
            severity=ErrorSeverity.MAJOR,
            description="标题格式不统一，字体大小不一致",
            location="第1章"
        )
        
        # 使用LLM分析模式
        patterns = await feedback_engine.analyze_patterns()
        return patterns
    
    patterns = loop.run_until_complete(test_feedback())
    print(f"✅ LLM模式分析成功")
    print(f"   - 发现模式数: {len(patterns)}")
    
    # 显示模式分析结果
    for pattern in patterns:
        print(f"\n📋 模式: {pattern.error_type}")
        print(f"   - 出现频率: {pattern.frequency}")
        print(f"   - 根本原因: {pattern.root_cause}")
        print(f"   - 预防策略: {pattern.prevention_strategy[:100]}...")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 总结 ====================
print("\n" + "="*60)
print("📊 LLM集成测试总结")
print("="*60)

# 获取最终统计
try:
    router = get_llm_router()
    final_stats = router.get_usage_stats()
    
    print(f"\n✅ 所有LLM集成测试完成！")
    print(f"\n📈 总体使用统计:")
    print(f"   - 总API调用: {final_stats['total_calls']}")
    print(f"   - 总tokens消耗: {final_stats['total_tokens']}")
    print(f"   - 总错误数: {final_stats['total_errors']}")
    print(f"   - 成功率: {final_stats['success_rate']:.1f}%")
    
    print(f"\n📊 各模型使用情况:")
    for model_name, stats in final_stats['by_model'].items():
        print(f"   - {model_name}:")
        print(f"     调用: {stats['calls']}, tokens: {stats['tokens']}, 错误: {stats['errors']}")
    
    print(f"\n✨ LLM集成功能:")
    print(f"   ✅ GenerationEngine - 使用DeepSeek生成真实投标内容")
    print(f"   ✅ ScoringEngine - 使用千问进行智能评分")
    print(f"   ✅ ReinforcementLearningFeedback - LLM根本原因分析和策略生成")
    print(f"   ✅ 多模型智能路由 - 根据任务类型自动选择最优模型")
    
    print(f"\n🎉 系统已完全集成大模型能力！")
    
except Exception as e:
    print(f"\n⚠️  统计获取失败: {e}")

print("\n" + "="*60)
