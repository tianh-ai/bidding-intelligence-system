#!/usr/bin/env python3
"""
简化版知识库测试 - 直接在 backend 目录运行
"""

import asyncio
import sys
from pathlib import Path

# 确保在 backend 目录
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from core.logger import logger
from core.mcp_client import get_knowledge_base_client
from core.ollama_client import get_ollama_client
from database import db


async def main():
    print("=" * 60)
    print("知识库 MCP 快速测试")
    print("=" * 60)
    print()
    
    # 1. Ollama 检查
    print("1. 检查 Ollama...")
    try:
        ollama = get_ollama_client()
        healthy = await ollama.check_health()
        if healthy:
            emb = await ollama.generate_embedding("测试")
            print(f"   ✓ Ollama 正常 (embedding 维度: {len(emb)})")
        else:
            print("   ✗ Ollama 不可用")
            return
    except Exception as e:
        print(f"   ✗ Ollama 错误: {e}")
        return
    
    # 2. 查询文件
    print("\n2. 查询已上传文件...")
    try:
        files = db.query("""
            SELECT id, filename, semantic_filename, created_at
            FROM uploaded_files
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if not files:
            print("   ✗ 无文件（请先上传）")
            return
        
        print(f"   ✓ 找到 {len(files)} 个文件:")
        for i, f in enumerate(files, 1):
            print(f"      {i}. {f['semantic_filename'] or f['filename']}")
        
        test_file = files[0]
    except Exception as e:
        print(f"   ✗ 查询失败: {e}")
        return
    
    # 3. MCP 知识库
    print(f"\n3. 查询知识库 (文件: {test_file['semantic_filename'] or test_file['filename']})...")
    try:
        kb = get_knowledge_base_client()
        
        result = await kb.list_knowledge_entries(
            file_id=test_file['id'],
            limit=10
        )
        
        entries = result.get('entries', [])
        total = result.get('total', 0)
        
        if total == 0:
            print("   ⚠ 该文件无知识条目")
        else:
            print(f"   ✓ 找到 {total} 条知识:")
            for i, e in enumerate(entries[:3], 1):
                print(f"      {i}. {e.get('title', '无标题')}")
    except Exception as e:
        print(f"   ✗ MCP 调用失败: {e}")
        logger.error(f"MCP 错误: {e}", exc_info=True)
        return
    
    # 4. 语义搜索
    print("\n4. 测试语义搜索...")
    try:
        if entries:
            query = entries[0].get('title', '测试')[:15]
        else:
            query = "测试"
        
        print(f"   查询: {query}")
        results = await kb.search_knowledge_semantic(
            query=query,
            limit=3,
            min_similarity=0.6
        )
        
        if results:
            print(f"   ✓ 找到 {len(results)} 个结果:")
            for i, r in enumerate(results, 1):
                sim = r.get('similarity', 0)
                print(f"      {i}. {r.get('title', '无标题')} (相似度: {sim:.3f})")
        else:
            print("   ⚠ 无结果（可能需要重建索引）")
    except Exception as e:
        print(f"   ✗ 搜索失败: {e}")
        return
    
    # 5. 统计
    print("\n5. 知识库统计...")
    try:
        stats = await kb.get_statistics()
        print(f"   总条目: {stats.get('total_entries', 0)}")
        print(f"   分类数: {stats.get('total_categories', 0)}")
    except Exception as e:
        print(f"   ⚠ 统计失败: {e}")
    
    print("\n" + "=" * 60)
    print("✓ 测试完成")
    print("=" * 60)
    print("\n物理存储:")
    print("  - 向量: PostgreSQL (pgvector)")
    print("  - MCP: mcp-servers/knowledge-base/")
    print("  - 模型: mxbai-embed-large (1024维)")


if __name__ == "__main__":
    asyncio.run(main())
