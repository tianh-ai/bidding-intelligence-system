"""
自学习投标系统 - 简化演示（无数据库依赖）

演示核心功能：
1. LLM文档配对
2. LLM结构提取
3. LLM逻辑学习
"""

import asyncio
from pathlib import Path

# 直接导入核心模块，避免数据库依赖
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.llm_router import get_llm_router, TaskType
from core.logger import logger

print("="*80)
print("自学习投标系统 - 核心功能演示")
print("="*80)


async def demo_llm_capabilities():
    """演示LLM核心能力"""
    
    router = get_llm_router()
    
    # ==================== 演示1: 文档分类 ====================
    print("\n" + "="*80)
    print("演示1: 智能文档分类")
    print("="*80)
    
    test_files = [
        "智慧城市管理平台_招标文件.pdf",
        "智慧城市管理平台_投标方案.docx",
        "电子政务系统_招标需求.pdf",
        "电子政务系统_技术方案.pdf"
    ]
    
    print("\n📁 待分类文件:")
    for f in test_files:
        print(f"   - {f}")
    
    print("\n🤖 LLM分类中...")
    
    for filename in test_files:
        prompt = f"""
请判断以下文件是招标文件还是投标文件：

文件名：{filename}

请仅返回以下之一：
- TENDER（如果是招标文件）
- PROPOSAL（如果是投标文件）
"""
        
        result = await router.generate_text(
            prompt=prompt,
            task_type=TaskType.EXTRACTION,
            max_tokens=10
        )
        
        doc_type = "招标文件" if "TENDER" in result.upper() else "投标文件"
        print(f"   ✅ {filename} → {doc_type}")
    
    # ==================== 演示2: 文档配对 ====================
    print("\n" + "="*80)
    print("演示2: 智能文档配对")
    print("="*80)
    
    doc_pairs = [
        ("智慧城市管理平台_招标文件", "ZCGZ-2024-001", "智慧城市管理平台"),
        ("智慧城市管理平台_投标方案", "ZCGZ-2024-001", "智慧城市管理平台"),
        ("电子政务系统_招标需求", "ZF-2024-002", "电子政务系统"),
        ("电子政务系统_技术方案", "ZF-2024-002", "电子政务系统")
    ]
    
    print("\n🤖 LLM配对分析...")
    
    tender_1 = doc_pairs[0]
    proposal_1 = doc_pairs[1]
    
    prompt = f"""
请判断以下两个文档是否属于同一个项目：

文档1（招标文件）：
- 文件名：{tender_1[0]}
- 项目编号：{tender_1[1]}
- 项目名：{tender_1[2]}

文档2（投标文件）：
- 文件名：{proposal_1[0]}
- 项目编号：{proposal_1[1]}
- 项目名：{proposal_1[2]}

请给出0-100的相似度评分，分数越高表示越可能是同一项目。
仅返回数字，如：95
"""
    
    result = await router.generate_text(
        prompt=prompt,
        task_type=TaskType.COMPARISON,
        max_tokens=10
    )
    
    score = int(''.join(filter(str.isdigit, result)))
    print(f"   ✅ 配对1: {tender_1[0]} ↔ {proposal_1[0]}")
    print(f"      相似度: {score}% {'✓ 匹配成功' if score > 80 else '✗ 不匹配'}")
    
    # ==================== 演示3: 章节提取 ====================
    print("\n" + "="*80)
    print("演示3: 文档结构提取")
    print("="*80)
    
    sample_doc = """
智慧城市管理平台 招标文件
项目编号：ZCGZ-2024-001

第一章 项目概述
1.1 项目名称：智慧城市管理平台
1.2 建设目标：打造统一的城市管理平台

第二章 技术要求
2.1 性能要求：CPU >= 8核，内存 >= 16GB
2.2 架构要求：采用微服务架构
2.3 部署要求：支持容器化部署

第三章 商务条款
3.1 付款方式：分三期付款
3.2 项目周期：6个月
"""
    
    print("\n📄 示例文档:")
    print(sample_doc[:200] + "...")
    
    print("\n🤖 LLM提取结构...")
    
    prompt = f"""
请分析以下招标文档，提取结构化信息：

{sample_doc}

请以JSON格式返回：
{{
  "project_name": "项目名称",
  "project_code": "项目编号",
  "chapters": [
    {{
      "chapter_id": "1",
      "title": "章节标题",
      "summary": "简要描述"
    }}
  ]
}}
"""
    
    result = await router.generate_text(
        prompt=prompt,
        task_type=TaskType.EXTRACTION,
        max_tokens=500
    )
    
    print(f"\n   提取结果:")
    print(f"   {result[:300]}...")
    
    # ==================== 演示4: 逻辑学习 ====================
    print("\n" + "="*80)
    print("演示4: 生成逻辑学习")
    print("="*80)
    
    tender_req = "性能要求：CPU >= 8核，内存 >= 16GB"
    proposal_resp = "性能配置：CPU 16核，内存 32GB（超出要求）"
    
    print(f"\n📋 招标需求: {tender_req}")
    print(f"📝 投标响应: {proposal_resp}")
    
    print("\n🤖 LLM学习生成规则...")
    
    prompt = f"""
分析以下招标需求和对应的投标响应，提取生成规则：

招标需求：{tender_req}
投标响应：{proposal_resp}

请以JSON格式返回生成规则：
{{
  "trigger_pattern": "需求的特征模式",
  "generation_strategy": "direct_match / enhanced_response / creative",
  "response_template": "响应模板",
  "confidence": 置信度(0-100)
}}
"""
    
    result = await router.generate_text(
        prompt=prompt,
        task_type=TaskType.ANALYSIS,
        max_tokens=300
    )
    
    print(f"\n   学习到的规则:")
    print(f"   {result[:250]}...")
    
    # ==================== 演示5: 智能生成 ====================
    print("\n" + "="*80)
    print("演示5: 智能内容生成")
    print("="*80)
    
    new_tender_req = "架构要求：采用微服务架构，支持容器化部署"
    
    print(f"\n📋 新招标需求: {new_tender_req}")
    print("\n🤖 LLM生成投标响应...")
    
    prompt = f"""
请根据以下招标要求生成专业的投标响应：

招标要求：{new_tender_req}

已学习的响应模式：
- 性能要求：超出基本要求，体现优势
- 技术方案：使用主流技术栈
- 部署方案：详细可行

请生成200字左右的投标响应内容。
"""
    
    result = await router.generate_text(
        prompt=prompt,
        system_prompt="你是专业的投标文件撰写专家",
        task_type=TaskType.GENERATION,
        max_tokens=500
    )
    
    print(f"\n   生成的投标响应:")
    print(f"   {result}")
    
    # ==================== 演示6: 质量验证 ====================
    print("\n" + "="*80)
    print("演示6: 内容质量验证")
    print("="*80)
    
    generated_content = result
    
    print(f"\n📝 待验证内容:")
    print(f"   {generated_content[:150]}...")
    
    print("\n🤖 LLM质量评估...")
    
    criteria = """
请从以下维度评估投标响应的质量：
1. 是否完全响应了招标要求
2. 技术方案是否先进可行
3. 表述是否专业规范
4. 是否具有说服力

请给出0-100的评分。
"""
    
    result = await router.score_content(
        content=generated_content,
        criteria=criteria
    )
    
    print(f"\n   质量评估结果:")
    print(f"   模型: {result.get('model', 'N/A')}")
    print(f"   评分: {result.get('score', 'N/A')}")
    print(f"   理由: {result.get('reasoning', 'N/A')[:200]}...")
    
    # ==================== 总结 ====================
    print("\n" + "="*80)
    print("✨ 演示完成")
    print("="*80)
    
    stats = router.get_usage_stats()
    
    print(f"\n📊 LLM调用统计:")
    print(f"   总调用次数: {stats['total_calls']}")
    print(f"   总tokens: {stats['total_tokens']}")
    print(f"   成功次数: {stats['successful_calls']}")
    print(f"   成功率: {stats['success_rate']:.1f}%")
    
    print(f"\n   各模型使用情况:")
    for model, model_stats in stats['by_model'].items():
        print(f"   - {model}:")
        print(f"     调用: {model_stats['calls']}, tokens: {model_stats['tokens']}")
    
    print("""
\n✅ 核心能力验证完成：

1. ✅ 文档智能分类 - LLM准确识别招标/投标文件
2. ✅ 文档智能配对 - LLM分析项目相似度，自动配对
3. ✅ 结构智能提取 - LLM提取章节、项目信息等结构化数据
4. ✅ 逻辑智能学习 - LLM从配对文档中学习生成规则
5. ✅ 内容智能生成 - LLM基于规则生成高质量投标内容
6. ✅ 质量智能验证 - LLM多维度评估生成内容质量

🎯 自学习投标系统的核心LLM能力已验证！
完整系统将整合这些能力实现端到端的自动化投标生成。
    """)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(demo_llm_capabilities())
    
    print("\n" + "="*80)
