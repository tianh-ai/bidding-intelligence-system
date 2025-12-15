#!/usr/bin/env python3
"""
Ollama 向量搜索快速测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from core.ollama_client import get_ollama_client
from core.logger import logger


async def test_ollama_connection():
    """测试 Ollama 连接"""
    print("=" * 50)
    print("测试 1: Ollama 服务连接")
    print("=" * 50)
    
    client = get_ollama_client()
    
    # 健康检查
    is_healthy = await client.check_health()
    if not is_healthy:
        print("❌ Ollama 服务不可用")
        print("   请确保 Ollama 正在运行: ollama serve")
        return False
    
    print("✓ Ollama 服务运行正常")
    
    # 列出可用模型
    models = await client.list_models()
    print(f"✓ 可用模型: {', '.join(models)}")
    
    if 'nomic-embed-text' not in [m.split(':')[0] for m in models]:
        print("⚠ 未找到 nomic-embed-text 模型")
        print("   下载模型: ollama pull nomic-embed-text")
        return False
    
    print("✓ nomic-embed-text 模型已安装")
    return True


async def test_embedding_generation():
    """测试 embedding 生成"""
    print("\n" + "=" * 50)
    print("测试 2: Embedding 生成")
    print("=" * 50)
    
    client = get_ollama_client()
    
    test_texts = [
        "投标保证金为项目总价的2%",
        "项目经理需要建造师执业资格证书",
        "技术方案应包含施工组织设计"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试文本 {i}: {text}")
        
        try:
            embedding = await client.generate_embedding(text)
            print(f"  ✓ Embedding 维度: {len(embedding)}")
            print(f"  ✓ 前5个值: {embedding[:5]}")
        except Exception as e:
            print(f"  ❌ 生成失败: {e}")
            return False
    
    return True


async def test_semantic_similarity():
    """测试语义相似度"""
    print("\n" + "=" * 50)
    print("测试 3: 语义相似度计算")
    print("=" * 50)
    
    client = get_ollama_client()
    
    # 测试查询和候选文本
    query = "项目经理需要什么资质？"
    candidates = [
        "项目负责人应具有建造师执业资格证书",
        "投标保证金为项目总价的2%",
        "施工现场应设置安全警示标志"
    ]
    
    print(f"\n查询: {query}")
    query_embedding = await client.generate_embedding(query)
    
    print("\n候选文本相似度:")
    for text in candidates:
        text_embedding = await client.generate_embedding(text)
        
        # 计算余弦相似度
        import numpy as np
        similarity = np.dot(query_embedding, text_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(text_embedding)
        )
        
        print(f"  [{similarity:.3f}] {text}")
    
    return True


async def test_knowledge_base_integration():
    """测试知识库集成"""
    print("\n" + "=" * 50)
    print("测试 4: 知识库 MCP 集成")
    print("=" * 50)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'mcp-servers' / 'knowledge-base' / 'python'))
        from knowledge_base import KnowledgeBaseMCP
        
        kb = KnowledgeBaseMCP()
        print("✓ KnowledgeBaseMCP 初始化成功")
        
        # 测试搜索（模拟）
        print("\n测试语义搜索方法...")
        print("  注意: 需要数据库连接和数据才能实际测试")
        
        return True
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n🚀 Ollama 向量搜索测试套件\n")
    
    results = []
    
    # 测试 1: 连接
    try:
        result = await test_ollama_connection()
        results.append(("Ollama 连接", result))
        if not result:
            print("\n⚠ 跳过后续测试（Ollama 不可用）")
            return
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        results.append(("Ollama 连接", False))
        return
    
    # 测试 2: Embedding 生成
    try:
        result = await test_embedding_generation()
        results.append(("Embedding 生成", result))
    except Exception as e:
        print(f"❌ Embedding 测试失败: {e}")
        results.append(("Embedding 生成", False))
    
    # 测试 3: 相似度计算
    try:
        result = await test_semantic_similarity()
        results.append(("语义相似度", result))
    except Exception as e:
        print(f"❌ 相似度测试失败: {e}")
        results.append(("语义相似度", False))
    
    # 测试 4: 知识库集成
    try:
        result = await test_knowledge_base_integration()
        results.append(("知识库集成", result))
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        results.append(("知识库集成", False))
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"  {status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！Ollama 向量搜索已准备就绪。")
        print("\n下一步:")
        print("  1. 启动后端服务: cd backend && python main.py")
        print("  2. 测试语义搜索 API:")
        print("     curl -X POST http://localhost:18888/api/knowledge/search/semantic \\")
        print("       -H 'Content-Type: application/json' \\")
        print("       -d '{\"query\": \"投标要求\", \"limit\": 5}'")
    else:
        print("\n⚠ 部分测试失败，请检查配置。")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
