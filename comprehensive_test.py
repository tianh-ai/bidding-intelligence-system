#!/usr/bin/env python3
"""
综合功能验证脚本
测试所有关键功能点
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_auth():
    """测试认证功能"""
    print_section("1. 测试认证功能")
    
    # 测试登录
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 登录成功")
        print(f"   用户: {data['user']['username']}")
        print(f"   角色: {data['user']['role']}")
        print(f"   Token: {data['token'][:50]}...")
        return data['token']
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def test_llm_models(token):
    """测试LLM模型API"""
    print_section("2. 测试LLM模型管理")
    
    response = requests.get(
        f"{BASE_URL}/api/llm/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        models = response.json()
        print(f"✅ 获取模型列表成功 ({len(models)} 个模型)")
        for model in models:
            print(f"   - {model['name']} ({model['id']})")
            print(f"     Provider: {model['provider']}")
            print(f"     Default: {'是' if model.get('is_default') else '否'}")
        return True
    else:
        print(f"❌ 获取模型列表失败: {response.text}")
        return False

def test_prompts(token):
    """测试提示词API"""
    print_section("3. 测试提示词管理")
    
    # 获取提示词模板
    response = requests.get(
        f"{BASE_URL}/api/prompts/templates",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✅ 获取提示词模板成功 ({len(templates)} 个)")
        for template in templates[:3]:  # 只显示前3个
            print(f"   - {template['title']} ({template['category']})")
    else:
        print(f"❌ 获取提示词失败: {response.text}")
        return False
    
    # 获取分类
    response = requests.get(
        f"{BASE_URL}/api/prompts/categories",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        categories = response.json()
        print(f"\n✅ 获取分类成功 ({len(categories)} 个)")
        for cat in categories:
            print(f"   - {cat['name']}: {cat['count']} 个模板")
        return True
    else:
        print(f"❌ 获取分类失败: {response.text}")
        return False

def test_file_upload(token):
    """测试文件上传"""
    print_section("4. 测试文件上传")
    
    # 创建测试文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是一个测试文件\n用于验证文件上传功能")
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'files': ('test.txt', f, 'text/plain')}
            data = {'doc_type': 'other'}
            
            response = requests.post(
                f"{BASE_URL}/api/files/upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 文件上传成功")
            print(f"   总文件数: {result.get('totalFiles', 0)}")
            if result.get('files'):
                for file in result['files']:
                    print(f"   - {file['name']} ({file['size']} bytes)")
            return True
        else:
            print(f"❌ 文件上传失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    finally:
        import os
        os.unlink(temp_file)

def test_health():
    """测试健康检查"""
    print_section("0. 系统健康检查")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 系统健康")
        print(f"   状态: {data['status']}")
        print(f"   服务: {data['service']}")
        return True
    else:
        print(f"❌ 系统不健康: {response.text}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  标书智能系统 - 综合功能验证")
    print("="*60)
    
    results = {}
    
    # 0. 健康检查
    results['health'] = test_health()
    if not results['health']:
        print("\n❌ 系统健康检查失败，停止测试")
        sys.exit(1)
    
    # 1. 认证测试
    token = test_auth()
    if not token:
        print("\n❌ 认证失败，停止测试")
        sys.exit(1)
    results['auth'] = True
    
    # 2. LLM模型测试
    results['llm'] = test_llm_models(token)
    
    # 3. 提示词测试
    results['prompts'] = test_prompts(token)
    
    # 4. 文件上传测试
    results['upload'] = test_file_upload(token)
    
    # 总结
    print_section("测试总结")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"总测试项: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print()
    
    for test, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print(f"⚠️  有 {total - passed} 项测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
