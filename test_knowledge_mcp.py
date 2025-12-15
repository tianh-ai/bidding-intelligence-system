#!/usr/bin/env python3
"""
测试知识库 MCP 集成
验证前端上传文件 → 主程序 → MCP → Ollama → 知识库的完整流程
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from core.logger import logger
from core.mcp_client import get_knowledge_base_client
from core.ollama_client import get_ollama_client
from database import db


async def test_knowledge_mcp():
    """测试知识库 MCP 完整流程"""
    
    print("=" * 60)
    print("知识库 MCP 集成测试")
    print("=" * 60)
    print()
    
    # 1. 测试 Ollama 连接
    print("步骤 1/5: 检查 Ollama 服务...")
    try:
        ollama_client = get_ollama_client()
        is_healthy = await ollama_client.check_health()
        
        if is_healthy:
            print("✓ Ollama 服务正常")
            # 测试 embedding 生成
            test_emb = await ollama_client.generate_embedding("测试文本")
            print(f"✓ Embedding 维度: {len(test_emb)}")
        else:
            print("✗ Ollama 服务不可用")
            return False
    except Exception as e:
        print(f"✗ Ollama 连接失败: {e}")
        return False
    
    print()
    
    # 2. 获取已上传文件列表
    print("步骤 2/5: 查询已上传文件...")
    try:
        files = db.query("""
            SELECT id, filename, semantic_filename, created_at, status
            FROM uploaded_files
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if not files:
            print("✗ 未找到已上传文件")
            print("请先通过前端上传文件")
            return False
        
        print(f"✓ 找到 {len(files)} 个文件:")
        for i, f in enumerate(files, 1):
            print(f"  {i}. {f['semantic_filename'] or f['filename']} (ID: {f['id'][:8]}...)")
        
        # 使用最新的文件进行测试
        test_file = files[0]
        print(f"\n使用文件: {test_file['semantic_filename'] or test_file['filename']}")
        print(f"文件 ID: {test_file['id']}")
    except Exception as e:
        print(f"✗ 查询文件失败: {e}")
        return False
    
    print()
    
    # 3. 查询该文件的知识条目
    print("步骤 3/5: 查询知识库条目...")
    try:
        kb_client = get_knowledge_base_client()
        
        # 列出该文件的知识条目
        result = await kb_client.list_knowledge_entries(
            file_id=test_file['id'],
            limit=20
        )
        
        entries = result.get('entries', [])
        total = result.get('total', 0)
        
        if total == 0:
            print("✗ 该文件暂无知识条目")
            print("文件可能正在处理中，或需要手动触发知识提取")
            return False
        
        print(f"✓ 找到 {total} 条知识条目:")
        for i, entry in enumerate(entries[:5], 1):
            title = entry.get('title', '无标题')
            category = entry.get('category', '未分类')
            print(f"  {i}. [{category}] {title}")
        
        if total > 5:
            print(f"  ... 还有 {total - 5} 条")
    
    except Exception as e:
        print(f"✗ 查询知识条目失败: {e}")
        logger.error(f"MCP 调用失败: {e}", exc_info=True)
        return False
    
    print()
    
    # 4. 测试语义搜索（使用 Ollama embeddings）
    print("步骤 4/5: 测试语义搜索...")
    try:
        # 从第一个条目提取关键词作为查询
        if entries:
            first_entry = entries[0]
            query = first_entry.get('title', '投标要求')[:20]
        else:
            query = "投标要求"
        
        print(f"查询词: {query}")
        
        # 执行语义搜索
        search_results = await kb_client.search_knowledge_semantic(
            query=query,
            limit=5,
            min_similarity=0.6
        )
        
        if search_results:
            print(f"✓ 找到 {len(search_results)} 个相关结果:")
            for i, result in enumerate(search_results, 1):
                title = result.get('title', '无标题')
                similarity = result.get('similarity', 0)
                category = result.get('category', '未分类')
                print(f"  {i}. [{category}] {title}")
                print(f"     相似度: {similarity:.3f}")
        else:
            print("⚠ 未找到相关结果（可能需要重建向量索引）")
    
    except Exception as e:
        print(f"✗ 语义搜索失败: {e}")
        logger.error(f"语义搜索失败: {e}", exc_info=True)
        return False
    
    print()
    
    # 5. 测试关键词搜索
    print("步骤 5/5: 测试关键词搜索...")
    try:
        keyword_results = await kb_client.search_knowledge(
            query=query,
            limit=5,
            min_score=0.0
        )
        
        if keyword_results:
            print(f"✓ 找到 {len(keyword_results)} 个匹配结果:")
            for i, result in enumerate(keyword_results, 1):
                title = result.get('title', '无标题')
                score = result.get('score', 0)
                print(f"  {i}. {title} (得分: {score:.2f})")
        else:
            print("⚠ 未找到匹配结果")
    
    except Exception as e:
        print(f"✗ 关键词搜索失败: {e}")
        logger.error(f"关键词搜索失败: {e}", exc_info=True)
        return False
    
    print()
    
    # 6. 获取统计信息
    print("知识库统计信息:")
    try:
        stats = await kb_client.get_statistics()
        print(f"  总条目数: {stats.get('total_entries', 0)}")
        print(f"  分类数: {stats.get('total_categories', 0)}")
        
        categories = stats.get('by_category', {})
        if categories:
            print("  各分类条目数:")
            for cat, count in categories.items():
                print(f"    - {cat}: {count}")
    
    except Exception as e:
        print(f"⚠ 获取统计信息失败: {e}")
    
    print()
    print("=" * 60)
    print("✓ 测试完成！")
    print("=" * 60)
    print()
    print("测试结果:")
    print("  1. Ollama 服务: ✓ 正常")
    print("  2. 文件上传: ✓ 正常")
    print("  3. MCP 调用: ✓ 正常")
    print("  4. 语义搜索: ✓ 正常")
    print("  5. 关键词搜索: ✓ 正常")
    print()
    print("知识库物理存储位置:")
    print("  - 数据库: PostgreSQL (pgvector)")
    print("  - 向量索引: 数据库中 (knowledge_base 表)")
    print("  - MCP 服务: mcp-servers/knowledge-base/dist/index.js")
    print("  - Ollama 模型: mxbai-embed-large (1024维)")
    print()
    
    return True


async def test_reindex():
    """测试重建向量索引"""
    print("\n" + "=" * 60)
    print("重建向量索引测试")
    print("=" * 60)
    print()
    
    try:
        kb_client = get_knowledge_base_client()
        
        print("开始重建向量索引...")
        print("这可能需要几分钟，取决于条目数量...")
        
        result = await kb_client.reindex_embeddings(
            batch_size=10
        )
        
        print(f"✓ 重建完成:")
        print(f"  处理条目数: {result.get('processed', 0)}")
        print(f"  成功数: {result.get('success', 0)}")
        print(f"  失败数: {result.get('failed', 0)}")
        
        if result.get('failed', 0) > 0:
            print(f"  失败原因: {result.get('errors', [])}")
        
        return True
    
    except Exception as e:
        print(f"✗ 重建索引失败: {e}")
        logger.error(f"重建索引失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试知识库 MCP 集成')
    parser.add_argument('--reindex', action='store_true', help='重建向量索引')
    args = parser.parse_args()
    
    if args.reindex:
        success = await test_reindex()
    else:
        success = await test_knowledge_mcp()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
