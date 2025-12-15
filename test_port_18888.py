#!/usr/bin/env python3
"""
使用正确端口 (18888) 测试知识库API
"""

import requests
import json

API_BASE = "http://localhost:18888"  # ← 正确的端口！

print("=" * 70)
print("知识库API测试 - 使用正确端口 18888")
print("=" * 70)

# 1. 测试连接
print("\n1. 测试后端连接")
try:
    response = requests.get(f"{API_BASE}/", timeout=5)
    print(f"✅ 连接成功 ({response.status_code})")
    print(f"   {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
    exit(1)

# 2. 登录
print("\n2. 登录获取token")
try:
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"username": "admin", "password": "bidding2024"},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ 登录成功")
        print(f"   Token: {token[:50]}...")
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"   {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ 登录错误: {e}")
    exit(1)

# 3. 测试知识库API
print("\n3. 测试知识库API")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# 3.1 统计
print("\n3.1 获取统计信息")
try:
    response = requests.get(
        f"{API_BASE}/api/knowledge/statistics",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 统计: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"⚠️  状态码: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 3.2 列表
print("\n3.2 获取知识条目列表")
try:
    response = requests.post(
        f"{API_BASE}/api/knowledge/entries/list",
        json={"limit": 5},
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        entries = data.get('entries', [])
        total = data.get('total', 0)
        
        print(f"✅ 总数: {total}")
        print(f"✅ 返回: {len(entries)} 条")
        
        if entries:
            print("\n示例条目:")
            for i, entry in enumerate(entries[:3], 1):
                print(f"\n{i}. {entry.get('title', '无标题')}")
                print(f"   类别: {entry.get('category')}")
                print(f"   文件: {entry.get('file_id')}")
                print(f"   内容: {entry.get('content', '')[:60]}...")
        else:
            print("\n⚠️  没有知识条目")
            print("请上传文件并等待处理完成")
    else:
        print(f"⚠️  状态码: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 70)
print("测试完成！")
print("\n如果API工作正常，请修改前端配置:")
print("  1. 编辑 frontend/.env")
print("  2. 设置: VITE_API_URL=http://localhost:18888")
print("  3. 重启前端: npm run dev")
print("=" * 70)
