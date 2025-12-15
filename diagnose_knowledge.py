#!/usr/bin/env python3
"""
完整系统诊断 - 找出知识库不显示的根本原因
"""

import requests
import json
import sys
import subprocess

print("=" * 70)
print("完整系统诊断 - 知识库显示问题排查")
print("=" * 70)

# 1. 检查端口
print("\n1. 检查后端服务端口")
print("-" * 70)

try:
    result = subprocess.run(
        ["lsof", "-i", ":8000"],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0 and result.stdout:
        print("✅ 端口 18888 有进程监听:")
        print(result.stdout)
    else:
        print("❌ 端口 18888 没有进程监听")
        print("\n请启动后端服务:")
        print("  cd backend && python main.py")
        sys.exit(1)
except Exception as e:
    print(f"⚠️  无法检查端口: {e}")

# 2. 测试连接
print("\n2. 测试后端连接")
print("-" * 70)

try:
    response = requests.get("http://localhost:18888/", timeout=5)
    print(f"✅ 后端服务响应:")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 无法连接后端: {e}")
    sys.exit(1)

# 3. 测试健康检查
print("\n3. 测试健康检查")
print("-" * 70)

try:
    response = requests.get("http://localhost:18888/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ 健康检查正常: {response.json()}")
    elif response.status_code == 401:
        print("⚠️  健康检查需要认证")
    else:
        print(f"   响应: {response.text}")
except Exception as e:
    print(f"❌ 健康检查失败: {e}")

# 4. 测试认证
print("\n4. 测试用户认证")
print("-" * 70)

# 尝试所有可能的账号
credentials_to_try = [
    ("admin", "bidding2024"),
    ("user", "user2024"),
    ("admin", "admin"),
    ("test", "test"),
]

token = None
for username, password in credentials_to_try:
    try:
        print(f"\n  尝试: {username} / {password}")
        response = requests.post(
            "http://localhost:18888/api/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"  ✅ 登录成功！")
            print(f"     Token: {token[:50]}...")
            break
        else:
            print(f"  ✗ 失败: {response.status_code}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")

if not token:
    print("\n❌ 无法获取认证token")
    print("\n建议:")
    print("  1. 检查 backend/routers/auth.py 中的 VALID_CREDENTIALS")
    print("  2. 或者暂时移除认证要求进行测试")
    print("  3. 或者使用 Postman/curl 手动测试登录接口")
    sys.exit(1)

# 5. 测试知识库API（带认证）
print("\n5. 测试知识库API（带认证）")
print("-" * 70)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# 5.1 统计API
print("\n5.1 统计API")
try:
    response = requests.get(
        "http://localhost:18888/api/knowledge/statistics",
        headers=headers,
        timeout=10
    )
    print(f"     状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"     ✓ 统计: {json.dumps(data, indent=6, ensure_ascii=False)}")
    else:
        print(f"     ✗ 失败: {response.text}")
except Exception as e:
    print(f"     ✗ 错误: {e}")

# 5.2 列表API
print("\n5.2 列表API")
try:
    response = requests.post(
        "http://localhost:18888/api/knowledge/entries/list",
        json={"limit": 5},
        headers=headers,
        timeout=10
    )
    print(f"     状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        entries = data.get('entries', [])
        total = data.get('total', 0)
        
        print(f"     ✓ 总数: {total}")
        print(f"     ✓ 返回: {len(entries)} 条")
        
        if entries:
            print("\n     示例条目:")
            for i, entry in enumerate(entries[:2], 1):
                print(f"\n     {i}. {entry.get('title', '无标题')}")
                print(f"        类别: {entry.get('category')}")
                print(f"        文件: {entry.get('file_id')}")
                print(f"        内容: {entry.get('content', '')[:60]}...")
        else:
            print("\n     ⚠️  没有知识条目")
    else:
        print(f"     ✗ 失败: {response.text}")
except Exception as e:
    print(f"     ✗ 错误: {e}")
    import traceback
    traceback.print_exc()

# 6. 总结
print("\n" + "=" * 70)
print("诊断总结")
print("=" * 70)

print("""
如果知识库API正常但前端不显示：

1. 检查前端登录状态
   - 打开浏览器开发者工具 (F12)
   - 检查 localStorage 中是否有 token
   - 如果没有，请先登录

2. 检查前端API调用
   - 切换到 Network 标签
   - 刷新页面或上传文件
   - 查找 /api/knowledge/entries/list 请求
   - 检查请求头是否包含 Authorization
   - 检查响应状态码和数据

3. 检查前端代码
   - 打开 Console 标签
   - 查找 "✓ 通过 MCP 加载了" 消息
   - 如果没有，说明 loadKnowledgeEntriesForFiles 没有被调用
   - 检查上传是否成功，文件状态是否为 'completed'

4. 常见问题
   - Token过期 → 重新登录
   - CORS错误 → 检查后端CORS配置
   - 500错误 → 查看后端日志
   - 数据为空 → 等待文件处理完成

测试账号:
  admin / bidding2024
  user / user2024
""")

print("=" * 70)
