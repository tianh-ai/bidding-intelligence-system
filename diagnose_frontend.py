#!/usr/bin/env python3
"""
前端代码诊断工具 - 检查FileUpload页面的完整性
"""
import re

def check_file_upload():
    print("=" * 60)
    print("前端 FileUpload.tsx 代码诊断")
    print("=" * 60)
    
    filepath = "frontend/src/pages/FileUpload.tsx"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "导入 knowledgeAPI": "knowledgeAPI" in content and "from '@/services/api'" in content,
        "定义 knowledgeEntries 状态": "const [knowledgeEntries" in content,
        "定义 documentIndexes 状态": "const [documentIndexes" in content,
        "loadKnowledgeEntriesForFiles 函数": "const loadKnowledgeEntriesForFiles" in content,
        "使用 MCP API": "knowledgeAPI.listEntries" in content,
        "loadSpecificDocumentIndexes 函数": "const loadSpecificDocumentIndexes" in content,
        "重复文件标记": "isDuplicate: true" in content,
        "文档目录 Tab": "key: 'indexes'" in content or "文档目录" in content,
        "知识库条目 Tab": "key: 'knowledge'" in content,
        "自动刷新逻辑": "setAutoRefresh" in content,
        "处理重复文件显示": "existing_size" in content and "existing_uploaded_at" in content,
    }
    
    print("\n✅ 通过的检查:")
    for name, passed in checks.items():
        if passed:
            print(f"   ✓ {name}")
    
    print("\n❌ 未通过的检查:")
    failed = False
    for name, passed in checks.items():
        if not passed:
            print(f"   ✗ {name}")
            failed = True
    
    if not failed:
        print("   (无)")
    
    # 检查关键函数调用
    print("\n" + "=" * 60)
    print("关键函数调用检查")
    print("=" * 60)
    
    function_calls = {
        "loadSpecificDocumentIndexes": re.findall(r'loadSpecificDocumentIndexes\([^)]*\)', content),
        "loadKnowledgeEntriesForFiles": re.findall(r'loadKnowledgeEntriesForFiles\([^)]*\)', content),
        "knowledgeAPI.listEntries": re.findall(r'knowledgeAPI\.listEntries\([^)]*\)', content, re.DOTALL)[:1],
    }
    
    for func, calls in function_calls.items():
        print(f"\n{func} 调用次数: {len(calls)}")
        if calls:
            print(f"   示例: {calls[0][:80]}...")
    
    # 统计代码行数
    lines = content.split('\n')
    print("\n" + "=" * 60)
    print(f"代码统计: 总共 {len(lines)} 行")
    print("=" * 60)
    
    # 检查是否有语法错误的迹象
    issues = []
    if content.count('console.log') > 15:
        issues.append(f"⚠ 发现 {content.count('console.log')} 个 console.log（可能需要清理）")
    
    duplicate_logs = re.findall(r'(console\.log\([^)]+\))\s*\1', content)
    if duplicate_logs:
        issues.append(f"⚠ 发现 {len(duplicate_logs)} 处重复的 console.log")
    
    if issues:
        print("\n潜在问题:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✓ 未发现明显问题")
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    check_file_upload()
