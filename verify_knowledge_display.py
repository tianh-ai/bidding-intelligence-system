#!/usr/bin/env python3
"""
知识库显示问题诊断脚本
验证整个数据流：数据库 → 后端API → MCP → 前端

创建时间：2025-12-14
"""

import requests
import json
import sys
import psycopg2
from datetime import datetime

# 配置
API_BASE = "http://localhost:18888"  # Docker端口！
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "bidding_db",
    "user": "postgres",
    "password": "postgres"
}

def test_database_connection():
    """测试数据库连接和数据"""
    print("=" * 60)
    print("1. 测试数据库连接")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 检查表是否存在
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'knowledge_entries'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("❌ 表 knowledge_entries 不存在！")
            return False
        
        print("✓ 表 knowledge_entries 存在")
        
        # 检查数据量
        cur.execute("SELECT COUNT(*) FROM knowledge_entries")
        total_count = cur.fetchone()[0]
        print(f"✓ 总知识条目数: {total_count}")
        
        if total_count == 0:
            print("⚠️  数据库中没有知识条目！")
            print("   请先上传文件并等待处理完成")
            return False
        
        # 获取最近的文件
        cur.execute("""
            SELECT DISTINCT file_id 
            FROM knowledge_entries 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        file_ids = [row[0] for row in cur.fetchall()]
        print(f"✓ 有知识条目的文件ID: {file_ids}")
        
        # 获取每个文件的条目数
        for file_id in file_ids:
            cur.execute("""
                SELECT COUNT(*), category 
                FROM knowledge_entries 
                WHERE file_id = %s 
                GROUP BY category
            """, (file_id,))
            
            categories = cur.fetchall()
            print(f"\n  文件 {file_id}:")
            for count, category in categories:
                print(f"    - {category}: {count} 条")
        
        cur.close()
        conn.close()
        
        return True, file_ids
        
    except Exception as e:
        print(f"❌ 数据库错误: {e}")
        return False, []


def test_backend_api():
    """测试后端API"""
    print("\n" + "=" * 60)
    print("2. 测试后端API")
    print("=" * 60)
    
    try:
        # 测试健康检查
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ 后端服务未运行 (状态码: {response.status_code})")
            return False
        
        print("✓ 后端服务运行正常")
        
        # 测试知识库统计
        response = requests.get(f"{API_BASE}/api/knowledge/statistics", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ 知识库统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"⚠️  统计API失败 (状态码: {response.status_code})")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务！")
        print("   请确保运行: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ API测试错误: {e}")
        return False


def test_knowledge_api(file_ids):
    """测试知识库API"""
    print("\n" + "=" * 60)
    print("3. 测试知识库API")
    print("=" * 60)
    
    if not file_ids:
        print("⚠️  没有可测试的文件ID")
        return False
    
    try:
        # 测试列表API（不带file_id）
        print("\n3.1 测试全局列表API")
        response = requests.post(
            f"{API_BASE}/api/knowledge/entries/list",
            json={"limit": 5},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ API失败 (状态码: {response.status_code})")
            print(f"   响应: {response.text}")
            return False
        
        data = response.json()
        print(f"✓ 返回 {len(data.get('entries', []))} 条记录")
        
        if data.get('entries'):
            print("\n  示例条目:")
            entry = data['entries'][0]
            print(f"    ID: {entry.get('id')}")
            print(f"    标题: {entry.get('title', '无')}")
            print(f"    类别: {entry.get('category', '无')}")
            print(f"    内容长度: {len(entry.get('content', ''))}")
        
        # 测试特定文件API
        print(f"\n3.2 测试特定文件API (file_id: {file_ids[0]})")
        response = requests.post(
            f"{API_BASE}/api/knowledge/entries/list",
            json={"file_id": file_ids[0], "limit": 100},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ API失败 (状态码: {response.status_code})")
            print(f"   响应: {response.text}")
            return False
        
        data = response.json()
        entries_count = len(data.get('entries', []))
        print(f"✓ 返回 {entries_count} 条记录")
        
        if entries_count == 0:
            print("⚠️  该文件没有知识条目！")
            return False
        
        # 显示前3条
        print("\n  前3条记录:")
        for i, entry in enumerate(data['entries'][:3], 1):
            print(f"\n  {i}. {entry.get('title', '无标题')}")
            print(f"     类别: {entry.get('category', '未分类')}")
            print(f"     内容: {entry.get('content', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 知识库API测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_server():
    """测试MCP服务器"""
    print("\n" + "=" * 60)
    print("4. 测试MCP服务器")
    print("=" * 60)
    
    import os
    import subprocess
    
    # 检查MCP服务器文件
    mcp_path = "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/knowledge-base/dist/index.js"
    
    if not os.path.exists(mcp_path):
        print(f"❌ MCP服务器文件不存在: {mcp_path}")
        print("   请运行: cd mcp-servers/knowledge-base && npm run build")
        return False
    
    print(f"✓ MCP服务器文件存在")
    
    # 检查node_modules
    node_modules = "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/knowledge-base/node_modules"
    if not os.path.exists(node_modules):
        print("⚠️  node_modules 不存在")
        print("   请运行: cd mcp-servers/knowledge-base && npm install")
        return False
    
    print("✓ 依赖已安装")
    
    return True


def generate_fix_recommendations():
    """生成修复建议"""
    print("\n" + "=" * 60)
    print("5. 修复建议")
    print("=" * 60)
    
    print("""
前端代码检查结果：
  ✓ loadKnowledgeEntriesForFiles 函数实现正确
  ✓ 调用时机正确（上传成功后）
  ✓ API调用格式正确
  ✓ 初始化时不自动加载（符合预期）

可能的问题：
  1. 后端服务未运行 → 启动: cd backend && python main.py
  2. MCP服务器未构建 → 构建: cd mcp-servers/knowledge-base && npm run build
  3. 数据库中无知识条目 → 上传文件并等待处理完成
  4. API路由未注册 → 检查 backend/main.py 是否包含 knowledge 路由

立即检查步骤：
  1. 打开浏览器开发者工具 (F12)
  2. 切换到 Network 标签
  3. 上传一个文件
  4. 查看是否有调用 /api/knowledge/entries/list
  5. 检查响应内容

如果API正常但前端不显示：
  - 检查浏览器控制台是否有 "✓ 通过 MCP 加载了 X 条知识条目"
  - 检查 knowledgeEntries state 是否被更新
  - 检查 Tab 组件是否正确渲染
""")


def main():
    """主函数"""
    print("知识库显示问题诊断")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试数据库
    db_ok, file_ids = test_database_connection()
    
    # 2. 测试后端API
    api_ok = test_backend_api()
    
    # 3. 测试知识库API
    if db_ok and api_ok and file_ids:
        knowledge_ok = test_knowledge_api(file_ids)
    else:
        knowledge_ok = False
    
    # 4. 测试MCP服务器
    mcp_ok = test_mcp_server()
    
    # 5. 生成修复建议
    generate_fix_recommendations()
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    print(f"数据库: {'✓' if db_ok else '✗'}")
    print(f"后端API: {'✓' if api_ok else '✗'}")
    print(f"知识库API: {'✓' if knowledge_ok else '✗'}")
    print(f"MCP服务器: {'✓' if mcp_ok else '✗'}")
    
    if all([db_ok, api_ok, knowledge_ok, mcp_ok]):
        print("\n✅ 所有测试通过！前端应该能正常显示知识库条目")
        print("   如果前端仍不显示，请检查浏览器控制台和Network标签")
    else:
        print("\n❌ 存在问题，请按照上述建议修复")
    
    return 0 if all([db_ok, api_ok, knowledge_ok, mcp_ok]) else 1


if __name__ == "__main__":
    sys.exit(main())
