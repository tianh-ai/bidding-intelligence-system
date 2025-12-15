#!/usr/bin/env python3
"""
诊断两个问题:
1. 为什么两个文件的目录解析不同
2. 为什么知识库不显示
"""

import sys
import os
sys.path.insert(0, '/app')

# 使用Docker端口18888
API_BASE = "http://localhost:18888"

print("=" * 80)
print("问题诊断: 目录解析 + 知识库显示")
print("=" * 80)
print()

# ============ 问题1: 目录解析差异 ============
print("【问题1】检查目录解析差异")
print("-" * 80)

try:
    from engines.parse_engine import ParseEngine
    from engines.parse_engine_v2 import EnhancedChapterExtractor
    
    # 测试文件
    pdf_path = '/app/./uploads/temp/b46e72a8/6f6f42e5-2689-42bc-8bad-32cedf4948cd.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"❌ 测试文件不存在: {pdf_path}")
        print()
    else:
        print(f"✓ 测试文件存在: {pdf_path}")
        print()
        
        # 使用ParseEngine解析
        print("1. 使用 ParseEngine 解析文档...")
        parser = ParseEngine()
        content = parser._parse_pdf(pdf_path)
        print(f"   提取文本长度: {len(content)} 字符")
        
        # 查看前500字符
        print(f"   前500字符预览:")
        print("   " + content[:500].replace('\n', '\n   '))
        print()
        
        # 使用v2提取器
        print("2. 使用 EnhancedChapterExtractor 提取章节...")
        extractor = EnhancedChapterExtractor()
        chapters = extractor.extract_chapters(content)
        
        print(f"   提取到 {len(chapters)} 个章节")
        print()
        
        # 显示前10个章节
        print("   前10个章节:")
        for i, ch in enumerate(chapters[:10]):
            print(f"   {i+1}. [{ch['chapter_level']}] {ch['chapter_number']} - {ch['chapter_title']}")
        print()
        
        # 检查是否有"第二部分"
        has_part2 = any('第二部分' in ch['chapter_number'] for ch in chapters)
        print(f"   是否找到'第二部分': {'✓ 是' if has_part2 else '❌ 否'}")
        
        # 检查是否有主章节(1. 2. 3.)
        main_chapters = [ch for ch in chapters if ch['chapter_level'] == 2 and ch['chapter_number'].isdigit()]
        print(f"   找到主章节(1. 2. 3.): {len(main_chapters)} 个")
        if main_chapters:
            print("   前5个主章节:")
            for ch in main_chapters[:5]:
                print(f"     - {ch['chapter_number']}. {ch['chapter_title']}")
        print()
        
except Exception as e:
    print(f"❌ 目录解析检查失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============ 问题2: 知识库显示 ============
print("【问题2】检查知识库显示")
print("-" * 80)

# 2.1 检查后端API是否可达
print("1. 检查后端API连接...")
try:
    import requests
    
    # 检查健康状态
    health_url = f"{API_BASE}/health"
    print(f"   测试: {health_url}")
    response = requests.get(health_url, timeout=5)
    print(f"   ✓ 后端健康状态: {response.status_code}")
    print()
    
    # 检查知识库API
    kb_health_url = f"{API_BASE}/api/knowledge/health"
    print(f"   测试: {kb_health_url}")
    response = requests.get(kb_health_url, timeout=5)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ 知识库API健康: {data}")
    else:
        print(f"   ❌ 知识库API异常: {response.text}")
    print()
    
    # 检查统计信息
    stats_url = f"{API_BASE}/api/knowledge/statistics"
    print(f"   测试: {stats_url}")
    response = requests.get(stats_url, timeout=5)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   知识库统计:")
        print(f"     - 总条目数: {data.get('total_entries', 0)}")
        print(f"     - 总文件数: {data.get('total_files', 0)}")
        print(f"     - MCP服务器: {data.get('mcp_server_status', 'unknown')}")
    else:
        print(f"   ❌ 获取统计失败: {response.text}")
    print()
    
except Exception as e:
    print(f"   ❌ API连接失败: {e}")
    print()

# 2.2 检查MCP服务器连接
print("2. 检查MCP知识库服务器...")
try:
    from core.mcp_client import get_knowledge_base_client
    
    kb_client = get_knowledge_base_client()
    print(f"   ✓ MCP客户端已初始化")
    print(f"   服务器路径: {kb_client.server_script_path if hasattr(kb_client, 'server_script_path') else 'N/A'}")
    print()
    
    # 尝试获取统计信息
    print("   测试MCP调用...")
    import asyncio
    
    async def test_mcp():
        try:
            stats = await kb_client.get_statistics()
            print(f"   ✓ MCP统计信息:")
            print(f"     - 总条目: {stats.get('total_entries', 0)}")
            print(f"     - 总文件: {stats.get('total_files', 0)}")
            return True
        except Exception as e:
            print(f"   ❌ MCP调用失败: {e}")
            return False
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(test_mcp())
    loop.close()
    print()
    
    if success:
        # 尝试列出知识条目
        print("   测试列出知识条目...")
        
        async def test_list():
            try:
                result = await kb_client.list_knowledge_entries(limit=5)
                entries = result.get('entries', [])
                print(f"   ✓ 列出了 {len(entries)} 条知识条目")
                
                if entries:
                    print("   前3条:")
                    for i, entry in enumerate(entries[:3]):
                        print(f"     {i+1}. ID: {entry.get('id', 'N/A')}")
                        print(f"        标题: {entry.get('title', 'N/A')[:50]}")
                        print(f"        文件: {entry.get('file_id', 'N/A')}")
                else:
                    print("   ⚠️  数据库中没有知识条目")
                    print("   提示: 需要先上传文件并处理才会生成知识条目")
            except Exception as e:
                print(f"   ❌ 列出失败: {e}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_list())
        loop.close()
        print()
        
except Exception as e:
    print(f"   ❌ MCP服务器检查失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============ 总结 ============
print("=" * 80)
print("诊断总结")
print("=" * 80)
print()
print("【问题1: 目录解析】")
print("可能原因:")
print("  1. ParseEngine和EnhancedChapterExtractor使用的文本提取方式不同")
print("  2. 正则表达式匹配规则不一致")
print("  3. 章节层级判断逻辑不同")
print()
print("【问题2: 知识库不显示】")
print("可能原因:")
print("  1. MCP服务器未启动或连接失败")
print("  2. 数据库中没有知识条目(需要先上传文件)")
print("  3. 前端API调用失败(检查网络控制台)")
print("  4. 端口配置错误(应使用18888)")
print()
print("建议操作:")
print("  1. 确保Docker服务正常运行: docker-compose ps")
print("  2. 检查后端日志: docker-compose logs backend")
print("  3. 上传测试文件并检查是否生成知识条目")
print("  4. 在浏览器开发者工具中检查API请求")
print()
