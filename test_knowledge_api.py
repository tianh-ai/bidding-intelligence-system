#!/usr/bin/env python3
"""
快速测试知识库API
找出知识条目不显示的原因
"""

import requests
import json
import sys

API_BASE = "http://localhost:18888"  # Docker端口！

def test_backend_health():
    """测试后端是否运行"""
    print("=" * 60)
    print("1. 测试后端服务")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        # 401 也说明服务在运行，只是需要认证
        if response.status_code in [200, 401]:
            print(f"✅ 后端服务运行正常 (状态码: {response.status_code})")
            if response.status_code == 401:
                print("   注意: 健康检查需要认证，但服务正常")
            return True
        else:
            print(f"❌ 后端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务！")
        print("   请运行: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_knowledge_api():
    """测试知识库API"""
    print("\n" + "=" * 60)
    print("2. 测试知识库API")
    print("=" * 60)
    
    # 测试1: 统计API
    print("\n2.1 测试统计API")
    try:
        response = requests.get(f"{API_BASE}/api/knowledge/statistics", timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   ✗ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False
    
    # 测试2: 列表API（不带file_id）
    print("\n2.2 测试列表API（全局）")
    try:
        response = requests.post(
            f"{API_BASE}/api/knowledge/entries/list",
            json={"limit": 5, "offset": 0},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get('entries', [])
            total = data.get('total', 0)
            print(f"   ✓ 总数: {total}")
            print(f"   ✓ 返回: {len(entries)} 条")
            
            if entries:
                print("\n   示例条目:")
                entry = entries[0]
                print(f"     ID: {entry.get('id')}")
                print(f"     标题: {entry.get('title', '无')}")
                print(f"     类别: {entry.get('category', '无')}")
                print(f"     文件ID: {entry.get('file_id', '无')}")
                print(f"     内容长度: {len(entry.get('content', ''))}")
            else:
                print("   ⚠️  数据库中没有知识条目")
                print("   原因可能是：")
                print("     1. 还没有上传过文件")
                print("     2. 文件上传后还在处理中")
                print("     3. 文档解析失败")
                return False
        else:
            print(f"   ✗ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试3: 健康检查
    print("\n2.3 测试MCP健康检查")
    try:
        response = requests.get(f"{API_BASE}/api/knowledge/health", timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ MCP状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   ✗ 失败: {response.text}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    return True


def test_file_list():
    """测试文件列表API"""
    print("\n" + "=" * 60)
    print("3. 测试文件列表API")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/files/list", timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            print(f"   ✓ 文件数量: {len(files)}")
            
            if files:
                print("\n   最近上传的文件:")
                for i, f in enumerate(files[:3], 1):
                    print(f"     {i}. {f.get('filename')} (ID: {f.get('id')})")
                    print(f"        状态: {f.get('status')}")
                    print(f"        上传时间: {f.get('uploaded_at')}")
                
                # 测试第一个文件的知识条目
                if files:
                    file_id = files[0].get('id')
                    print(f"\n   测试文件 {file_id} 的知识条目:")
                    
                    response = requests.post(
                        f"{API_BASE}/api/knowledge/entries/list",
                        json={"file_id": file_id, "limit": 10},
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        entries = data.get('entries', [])
                        print(f"     ✓ 知识条目数: {len(entries)}")
                        
                        if not entries:
                            print(f"     ⚠️  该文件没有知识条目")
                            print(f"     请检查文件状态是否为 'completed'")
                    else:
                        print(f"     ✗ 失败: {response.text}")
            else:
                print("   ⚠️  没有已上传的文件")
                print("   请先上传一个文件测试")
        else:
            print(f"   ✗ 失败: {response.text}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")


def main():
    """主函数"""
    print("知识库API快速测试")
    print(f"时间: {json.dumps(__import__('datetime').datetime.now().isoformat())}")
    print()
    
    # 1. 测试后端
    if not test_backend_health():
        print("\n❌ 后端服务未运行，无法继续测试")
        return 1
    
    # 2. 测试知识库API
    if not test_knowledge_api():
        print("\n❌ 知识库API测试失败")
        return 1
    
    # 3. 测试文件列表
    test_file_list()
    
    print("\n" + "=" * 60)
    print("诊断建议")
    print("=" * 60)
    print("""
如果知识库API返回空数据：
  1. 检查是否上传过文件
  2. 检查文件状态是否为 'completed'
  3. 检查后端日志是否有解析错误
  4. 检查数据库: SELECT COUNT(*) FROM knowledge_entries;

如果前端仍然不显示：
  1. 打开浏览器开发者工具 (F12)
  2. 切换到 Console 标签
  3. 查找 "✓ 通过 MCP 加载了" 消息
  4. 切换到 Network 标签
  5. 查看 /api/knowledge/entries/list 请求
  6. 检查响应数据

常见问题：
  - API返回200但前端不显示 → 检查前端state更新逻辑
  - API返回空数组 → 数据库中没有知识条目，需要等待文件处理完成
  - API返回500错误 → 检查MCP服务器是否正常，查看后端日志
""")
    
    print("\n✅ 测试完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
