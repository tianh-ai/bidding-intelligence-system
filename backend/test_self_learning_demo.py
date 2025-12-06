"""
自学习投标系统 - 完整演示

演示完整的工作流：
1. 批量上传招投标文件
2. 自动配对和学习
3. 生成新投标文件
4. 人工验证反馈
5. 系统自我优化
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 直接导入，避免engines/__init__.py的数据库依赖
import importlib.util

spec = importlib.util.spec_from_file_location(
    "self_learning_system",
    backend_dir / "engines" / "self_learning_system.py"
)
self_learning_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(self_learning_module)

SelfLearningBiddingSystem = self_learning_module.SelfLearningBiddingSystem

from core.logger import logger

print("="*80)
print("自学习投标系统 - 完整演示")
print("="*80)


async def demo_complete_workflow():
    """演示完整工作流"""
    
    # 初始化系统
    print("\n📦 初始化自学习投标系统...")
    system = SelfLearningBiddingSystem(storage_root="data/demo_self_learning")
    
    # ==================== 阶段1: 批量学习 ====================
    print("\n" + "="*80)
    print("阶段1: 批量学习 - 从历史文件构建逻辑库")
    print("="*80)
    
    # 模拟历史招投标文件
    print("\n📁 准备历史文件...")
    print("   - 项目A: 招标文件 + 投标文件（已中标）")
    print("   - 项目B: 招标文件 + 投标文件（已中标）")
    print("   - 项目C: 招标文件 + 投标文件（已中标）")
    
    # 创建模拟文件
    demo_files_dir = Path("data/demo_files")
    demo_files_dir.mkdir(parents=True, exist_ok=True)
    
    demo_files = []
    
    # 项目A
    tender_a = demo_files_dir / "项目A_招标文件.txt"
    tender_a.write_text("""
智慧城市管理平台 招标文件
项目编号：ZCGZ-2024-001

第一章 项目概述
1.1 项目名称：智慧城市管理平台
1.2 建设目标：打造统一的城市管理平台

第二章 技术要求
2.1 性能要求：CPU >= 8核，内存 >= 16GB
2.2 架构要求：采用微服务架构
2.3 部署要求：支持容器化部署
""", encoding='utf-8')
    demo_files.append(str(tender_a))
    
    proposal_a = demo_files_dir / "项目A_投标文件.txt"
    proposal_a.write_text("""
智慧城市管理平台 投标方案
项目编号：ZCGZ-2024-001

第一章 项目理解
我们深入理解项目需求，将打造一流的智慧城市管理平台。

第二章 技术方案
2.1 性能配置：CPU 16核，内存 32GB（超出要求）
2.2 技术架构：采用Spring Cloud微服务架构
2.3 部署方案：基于Kubernetes的容器化部署方案
""", encoding='utf-8')
    demo_files.append(str(proposal_a))
    
    # 项目B
    tender_b = demo_files_dir / "项目B_招标需求.txt"
    tender_b.write_text("""
电子政务系统 招标需求
招标编号：ZF-2024-002

第一章 需求说明
1.1 系统名称：电子政务平台
1.2 业务范围：政务审批、公文流转

第二章 技术标准
2.1 数据库：支持PostgreSQL
2.2 安全要求：通过等保三级认证
""", encoding='utf-8')
    demo_files.append(str(tender_b))
    
    proposal_b = demo_files_dir / "项目B_技术方案.txt"
    proposal_b.write_text("""
电子政务系统 技术方案
项目编号：ZF-2024-002

第一章 方案概述
针对电子政务平台需求，我们提供完整解决方案。

第二章 技术实现
2.1 数据库方案：PostgreSQL 14 高可用集群
2.2 安全方案：符合等保三级要求，包含加密、审计等
""", encoding='utf-8')
    demo_files.append(str(proposal_b))
    
    print(f"\n✅ 准备了 {len(demo_files)} 个历史文件")
    
    # 开始批量学习
    print("\n🧠 开始批量学习...")
    print("   步骤1: 智能配对招标-投标文件")
    print("   步骤2: 解析文档结构")
    print("   步骤3: 生成知识库")
    print("   步骤4: 学习生成逻辑")
    print("   步骤5: 学习验证逻辑")
    
    learn_result = await system.batch_learn_from_files(demo_files)
    
    print(f"\n📊 学习结果:")
    print(f"   ✅ 处理配对: {learn_result.get('pairs_processed', 0)}")
    print(f"   ✅ 知识库: {learn_result.get('knowledge_bases', 0)}")
    print(f"   ✅ 生成规则: {learn_result.get('generation_rules', 0)}")
    print(f"   ✅ 验证规则: {learn_result.get('validation_rules', 0)}")
    print(f"   📈 平均成功率: {learn_result.get('avg_success_rate', 0):.1f}%")
    
    # ==================== 阶段2: 智能生成 ====================
    print("\n" + "="*80)
    print("阶段2: 智能生成 - 为新招标文件生成投标文件")
    print("="*80)
    
    # 创建新的招标文件
    print("\n📄 新招标文件到来...")
    new_tender = demo_files_dir / "项目C_新招标.txt"
    new_tender.write_text("""
数字化办公平台 招标文件
项目编号：DB-2024-003

第一章 项目背景
1.1 项目名称：数字化办公平台
1.2 目标：提升办公效率

第二章 技术要求
2.1 性能：CPU >= 8核
2.2 架构：微服务架构
2.3 安全：等保三级
""", encoding='utf-8')
    
    print(f"   招标文件: {new_tender.name}")
    print(f"   项目编号: DB-2024-003")
    
    print("\n🤖 启动智能生成...")
    print("   使用: 生成逻辑库 + 验证逻辑库 + 知识库")
    print("   策略: 迭代优化，最多5次")
    print("   目标: 质量分数 >= 90")
    
    gen_result = await system.generate_proposal_for_tender(
        tender_file_path=str(new_tender),
        max_iterations=5,
        quality_threshold=90.0
    )
    
    if gen_result.get('status') == 'success':
        print(f"\n✅ 投标文件生成成功!")
        print(f"   📝 提案ID: {gen_result.get('proposal_id', 'N/A')}")
        print(f"   📊 质量分数: {gen_result.get('quality_score', 0):.1f}")
        print(f"   🔄 迭代次数: {gen_result.get('iterations', 0)}")
        print(f"   📑 章节数: {gen_result.get('chapters', 0)}")
        print(f"   💾 存储路径: {gen_result.get('storage_path', 'N/A')}")
        print(f"\n   自我检查:")
        self_check = gen_result.get('self_check', {})
        print(f"   - 通过: {self_check.get('passed', 0)} / {self_check.get('total', 0)}")
        print(f"   - 失败: {self_check.get('failed', 0)}")
    else:
        print(f"\n❌ 生成失败: {gen_result.get('message', 'Unknown error')}")
    
    # ==================== 阶段3: 人工验证反馈 ====================
    print("\n" + "="*80)
    print("阶段3: 人工验证与反馈循环")
    print("="*80)
    
    print("\n👤 人工验证中...")
    print("   专家审阅生成的投标文件")
    
    # 模拟人工反馈
    human_feedback = {
        "approved": True,
        "quality_rating": 88.0,
        "issues": [
            {
                "type": "warning",
                "description": "第二章技术方案可以更详细",
                "chapter": "2"
            }
        ],
        "suggestions": [
            "增加案例说明",
            "补充技术架构图"
        ]
    }
    
    print(f"\n📋 人工反馈:")
    print(f"   结果: {'✅ 通过' if human_feedback['approved'] else '❌ 拒绝'}")
    print(f"   评分: {human_feedback['quality_rating']}")
    print(f"   问题: {len(human_feedback['issues'])}")
    print(f"   建议: {len(human_feedback['suggestions'])}")
    
    if gen_result.get('status') == 'success':
        proposal_id = gen_result.get('proposal_id')
        
        print(f"\n🔄 将反馈用于优化逻辑库...")
        
        feedback_result = await system.refine_with_human_feedback(
            proposal_id=proposal_id,
            human_feedback=human_feedback
        )
        
        print(f"\n✅ 逻辑库已更新:")
        updates = feedback_result.get('updates', {})
        print(f"   - 生成规则更新: {updates.get('generation_rules_updated', 0)}")
        print(f"   - 验证规则新增: {updates.get('validation_rules_added', 0)}")
        print(f"   - 知识条目新增: {updates.get('knowledge_entries_added', 0)}")
    
    # ==================== 系统统计 ====================
    print("\n" + "="*80)
    print("系统统计信息")
    print("="*80)
    
    stats = system.get_system_stats()
    
    print(f"\n📊 整体统计:")
    print(f"   知识库数量: {stats.get('knowledge_bases', 0)}")
    print(f"   知识条目总数: {stats.get('total_kb_entries', 0)}")
    
    gen_logic = stats.get('generation_logic')
    if gen_logic:
        print(f"\n   生成逻辑库:")
        print(f"   - 规则总数: {gen_logic.get('total_rules', 0)}")
        print(f"   - 平均成功率: {gen_logic.get('avg_success_rate', 0):.1f}%")
    
    val_logic = stats.get('validation_logic')
    if val_logic:
        print(f"\n   验证逻辑库:")
        print(f"   - 规则总数: {val_logic.get('total_rules', 0)}")
        print(f"   - 平均精确率: {val_logic.get('avg_precision', 0):.1f}%")
    
    print(f"\n   💾 数据存储: {stats.get('storage_root', 'N/A')}")
    
    # ==================== 总结 ====================
    print("\n" + "="*80)
    print("✨ 演示完成")
    print("="*80)
    
    print("""
完整的自学习循环已展示：

1. ✅ 批量学习
   - 自动配对招投标文件
   - 提取结构化知识
   - 学习生成和验证逻辑

2. ✅ 智能生成
   - 基于逻辑库生成投标文件
   - 自我验证和迭代优化
   - 达到质量阈值

3. ✅ 反馈循环
   - 人工验证和打分
   - 反馈用于优化逻辑库
   - 持续改进生成质量

4. ✅ 知识积累
   - 知识库不断扩充
   - 逻辑库越来越精准
   - 生成质量持续提升

🎯 系统已实现完全自学习！
    """)


if __name__ == "__main__":
    # 运行演示
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(demo_complete_workflow())
    
    print("\n" + "="*80)
