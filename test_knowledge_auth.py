#!/usr/bin/env python3
"""
带认证的知识库API测试
"""

import requests
import json
import sys

API_BASE = "http://localhost:18888"  # Docker端口！

def login():
    """登录获取token"""
    print("登录中...")
    try:
        # 使用正确的测试账号
        response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={"username": "admin", "password": "bidding2024"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ 登录成功，获取token")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
            # 尝试user账号
            print("\n尝试user账号...")
            response = requests.post(
                f"{API_BASE}/api/auth/login",
                json={"username": "user", "password": "user2024"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                print(f"✅ 测试账号登录成功")
                return token
            
            return None
    except Exception as e:
        print(f"❌ 登录错误: {e}")
        return None


def test_knowledge_api_with_auth(token):
    """测试知识库API（带认证）"""
    print("\n" + "=" * 60)
    print("测试知识库API（带认证）")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 测试1: 统计API
    print("\n1. 测试统计API")
    try:
        response = requests.get(
            f"{API_BASE}/api/knowledge/statistics",
            headers=headers,
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   ✗ 失败: {response.text}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    # 测试2: 列表API
    print("\n2. 测试列表API")
    try:
        response = requests.post(
            f"{API_BASE}/api/knowledge/entries/list",
            json={"limit": 10, "offset": 0},
            headers=headers,
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
                print("\n   前3条记录:")
                for i, entry in enumerate(entries[:3], 1):
                    print(f"\n   {i}. {entry.get('title', '无标题')}")
                    print(f"      类别: {entry.get('category', '未分类')}")
                    print(f"      文件: {entry.get('file_id', '无')}")
                    print(f"      内容: {entry.get('content', '')[:80]}...")
                
                return True
            else:
                print("\n   ⚠️  数据库中没有知识条目")
                print("   可能原因：")
                print("     1. 还没上传过文件")
                print("     2. 文件正在处理中")
                print("     3. 文档解析失败")
                
                # 检查文件列表
                print("\n   检查文件列表...")
                response = requests.get(
                    f"{API_BASE}/api/files",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    files_data = response.json()
                    files = files_data.get('files', [])
                    print(f"     文件数量: {len(files)}")
                    
                    if files:
                        print("     文件列表:")
                        for f in files[:5]:
                            print(f"       - {f.get('filename')} (状态: {f.get('status')})")
                    else:
                        print("     ⚠️  没有上传的文件")
                        print("     请先上传文件以测试知识库功能")
                
                return False
        else:
            print(f"   ✗ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("知识库API认证测试")
    print("=" * 60)
    
    # 登录
    token = login()
    if not token:
        print("\n❌ 无法获取认证token")
        print("\n提示:")
        print("  1. 确保后端服务运行: cd backend && python main.py")
        print("  2. 确保有测试账号 (admin/admin123 或 test/test123)")
        print("  3. 或者检查 backend/routers/auth.py 的登录逻辑")
        return 1
    
    # 测试知识库API
    success = test_knowledge_api_with_auth(token)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 知识库API工作正常，有数据返回")
        print("\n如果前端不显示知识条目，请检查:")
        print("  1. 前端是否正确登录并获取token")
        print("  2. 浏览器控制台是否有错误")
        print("  3. Network标签中API调用是否成功")
        print("  4. 前端state是否正确更新")
    else:
        print("⚠️  知识库API正常但没有数据")
        print("\n下一步:")
        print("  1. 上传一个PDF文件")
        print("  2. 等待文件状态变为 'completed'")
        print("  3. 再次运行此测试")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
