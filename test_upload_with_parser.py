"""
测试文件上传流程和新的章节内容提取功能
"""

import requests
import json
from pathlib import Path

API_BASE = "http://localhost:18888/api"

# 1. 准备测试文件
test_file = Path("test_bidding_doc.txt")
if not test_file.exists():
    print(f"❌ 测试文件不存在: {test_file}")
    exit(1)

print("=" * 80)
print("测试文件上传和章节内容提取")
print("=" * 80)

# 2. 上传文件
print("\n[步骤1] 上传测试文件")
print("-" * 80)

with open(test_file, 'rb') as f:
    files = {'files': (test_file.name, f, 'text/plain')}
    data = {
        'uploader': 'test_user',
        'duplicate_action': 'overwrite'
    }
    
    response = requests.post(
        f"{API_BASE}/files/upload",
        files=files,
        data=data
    )

if response.status_code == 200:
    result = response.json()
    print(f"✅ 上传成功!")
    print(f"   Session ID: {result.get('session_id')}")
    
    uploaded = result.get('uploaded', [])
    if uploaded:
        file_info = uploaded[0]
        file_id = file_info.get('id')
        print(f"   File ID: {file_id}")
        print(f"   文件名: {file_info.get('name')}")
        print(f"   状态: {file_info.get('status')}")
        
        # 3. 等待解析完成
        import time
        print("\n[步骤2] 等待文件解析（5秒）")
        print("-" * 80)
        time.sleep(5)
        
        # 4. 查询章节信息
        print("\n[步骤3] 查询章节信息")
        print("-" * 80)
        
        # 直接查询数据库
        import sys
        sys.path.insert(0, 'backend')
        from database import db
        
        chapters = db.query("""
            SELECT 
                id,
                chapter_number,
                chapter_title,
                chapter_level,
                LENGTH(content) as content_length,
                LEFT(content, 100) as content_preview,
                structure_data
            FROM chapters
            WHERE file_id = %s
            ORDER BY id
        """, (file_id,))
        
        print(f"✅ 找到 {len(chapters)} 个章节:\n")
        
        has_content = False
        has_structure_data = False
        
        for i, ch in enumerate(chapters[:10]):  # 只显示前10个
            print(f"章节 {i+1}:")
            print(f"  编号: {ch['chapter_number']}")
            print(f"  标题: {ch['chapter_title']}")
            print(f"  级别: L{ch['chapter_level']}")
            print(f"  内容长度: {ch['content_length']} 字符")
            
            if ch['content_length'] > 0:
                has_content = True
                preview = ch['content_preview'].replace('\n', ' ')
                print(f"  内容预览: {preview}...")
            else:
                print(f"  ⚠️  内容为空")
            
            if ch['structure_data'] and ch['structure_data'] != {}:
                has_structure_data = True
                print(f"  格式数据: {json.dumps(ch['structure_data'], ensure_ascii=False)[:100]}...")
            else:
                print(f"  ⚠️  格式数据为空")
            print()
        
        # 总结
        print("\n" + "=" * 80)
        print("测试结果总结")
        print("=" * 80)
        
        if has_content:
            print("✅ 章节内容提取成功（修复生效）")
        else:
            print("❌ 章节内容仍为空（修复失败）")
        
        if has_structure_data:
            print("✅ 格式信息提取成功")
        else:
            print("⚠️  格式信息未提取（可能是TXT文件不支持）")
        
        print(f"\n修复验证:")
        print(f"  - 章节总数: {len(chapters)}")
        print(f"  - 包含内容的章节: {sum(1 for ch in chapters if ch['content_length'] > 0)}")
        print(f"  - 内容覆盖率: {sum(1 for ch in chapters if ch['content_length'] > 0) / len(chapters) * 100:.1f}%")
        
    else:
        print("❌ 上传失败，没有返回文件信息")
        print(f"   Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
else:
    print(f"❌ 上传失败: {response.status_code}")
    print(f"   Error: {response.text}")
