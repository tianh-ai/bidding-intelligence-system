#!/usr/bin/env python3
"""
知识库测试 - 在 backend 目录直接运行
"""

import asyncio
import sys

from core.logger import logger
from core.mcp_client import get_knowledge_base_client
from core.ollama_client import get_ollama_client
from database import db


async def main():
    print("=" * 60)
    print("知识库 MCP 测试")
    print("=" * 60)
    print()
    
    # 1. Ollama
    print("1. 检查 Ollama...")
    try:
        ollama = get_ollama_client()
        healthy = await ollama.check_health()
        if healthy:
            emb = await ollama.generate_embedding("测试")
            print(f"   ✓ Ollama 正常 (embedding: {len(emb)}维)")
        else:
            print("   ✗ Ollama 不可用")
            return
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return
    
    # 2. 查文件
    print("\n2. 查询已上传文件...")
    try:
        files = db.query("""
            SELECT id, filename, semantic_filename
            FROM uploaded_files
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if not files:
            print("   ✗ 无文件")
            return
        
        print(f"   ✓ {len(files)} 个文件:")
        for i, f in enumerate(files, 1):
            print(f"      {i}. {f['semantic_filename'] or f['filename']}")
        
        test_file = files[0]
    except Exception as e:
        print(f"   ✗ 失败: {e}")
        return
    
    # 3. MCP
    print(f"\n3. MCP 知识库...")
    try:
        kb = get_knowledge_base_client()
        result = await kb.list_knowledge_entries(
            file_id=test_file['id'],
            limit=10
        )
        
        entries = result.get('entries', [])
        total = result.get('total', 0)
        
        if total == 0:
            print("   ⚠ 无知识条目")
        else:
            print(f"   ✓ {total} 条知识:")
            for i, e in enumerate(entries[:3], 1):
                print(f"      {i}. {e.get('title', '?')}")
    except Exception as e:
        print(f"   ✗ MCP 失败: {e}")
        logger.error("MCP error", exc_info=True)
        return
    
    # 4. 语义搜索
    print("\n4. 语义搜索...")
    try:
        query = entries[0].get('title', '测试')[:15] if entries else "测试"
        print(f"   查询: {query}")
        
        results = await kb.search_knowledge_semantic(
            query=query,
            limit=3,
            min_similarity=0.6
        )
        
        if results:
            print(f"   ✓ {len(results)} 个结果:")
            for i, r in enumerate(results, 1):
                print(f"      {i}. {r.get('title', '?')} ({r.get('similarity', 0):.3f})")
        else:
            print("   ⚠ 无结果")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
    
    # 5. 统计
    print("\n5. 统计...")
    try:
        stats = await kb.get_statistics()
        print(f"   总数: {stats.get('total_entries', 0)}")
        print(f"   分类: {stats.get('total_categories', 0)}")
    except Exception as e:
        print(f"   ⚠ {e}")
    
    print("\n" + "=" * 60)
    print("✓ 完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
