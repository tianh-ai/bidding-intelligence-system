#!/usr/bin/env python3
"""
查询前端上传文件的知识库条目
"""
import asyncio
import sys
sys.path.insert(0, '/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend')

from core.mcp_client import get_knowledge_base_client
from database import db


async def main():
    # 获取最新的两个文件
    files = db.query("""
        SELECT id, filename, semantic_filename, doc_type, created_at
        FROM uploaded_files
        ORDER BY created_at DESC
        LIMIT 2
    """)
    
    if not files:
        print("未找到文件")
        return
    
    kb = get_knowledge_base_client()
    
    for i, f in enumerate(files, 1):
        print(f"\n{'='*60}")
        print(f"文件 {i}: {f['semantic_filename'] or f['filename']}")
        print(f"类型: {f['doc_type']}")
        print(f"ID: {f['id']}")
        print('='*60)
        
        # 查询知识条目
        result = await kb.list_knowledge_entries(
            file_id=f['id'],
            limit=20
        )
        
        entries = result.get('entries', [])
        total = result.get('total', 0)
        
        if total == 0:
            print("⚠ 该文件暂无知识条目")
            print("\n建议：运行知识提取")
            print(f"curl -X POST http://localhost:18888/api/files/{f['id']}/extract-knowledge")
        else:
            print(f"\n✓ 找到 {total} 条知识条目:\n")
            for j, entry in enumerate(entries, 1):
                print(f"{j}. [{entry.get('category', '?')}] {entry.get('title', '无标题')}")
                print(f"   内容: {entry.get('content', '')[:80]}...")
                print(f"   重要性: {entry.get('importance_score', 0):.1f}")
                if entry.get('keywords'):
                    print(f"   关键词: {', '.join(entry['keywords'][:5])}")
                print()

asyncio.run(main())
