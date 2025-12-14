#!/usr/bin/env python3
"""
简化的模块导入测试（不依赖数据库连接）
"""

import sys
import ast
from pathlib import Path

def check_syntax(filepath):
    """检查 Python 文件语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, "✅ 语法正确"
    except SyntaxError as e:
        return False, f"❌ 语法错误: {e}"
    except Exception as e:
        return False, f"❌ 错误: {e}"

def check_file_exists(filepath):
    """检查文件是否存在"""
    return Path(filepath).exists()

def main():
    print("="*60)
    print("🔍 文档处理系统模块检查")
    print("="*60)
    
    # 要检查的模块
    modules = [
        'backend/engines/smart_document_classifier.py',
        'backend/engines/ocr_extractor.py',
        'backend/engines/document_processor.py'
    ]
    
    all_ok = True
    
    for module_path in modules:
        print(f"\n📄 {module_path}")
        
        # 检查文件存在
        if not check_file_exists(module_path):
            print(f"  ❌ 文件不存在")
            all_ok = False
            continue
        
        # 检查语法
        ok, msg = check_syntax(module_path)
        print(f"  {msg}")
        
        if not ok:
            all_ok = False
            continue
        
        # 检查文件大小
        size = Path(module_path).stat().st_size
        print(f"  📊 文件大小: {size} 字节")
    
    # 检查数据库模式
    print(f"\n📄 backend/database/document_processing_schema.sql")
    schema_file = 'backend/database/document_processing_schema.sql'
    
    if check_file_exists(schema_file):
        size = Path(schema_file).stat().st_size
        print(f"  ✅ 文件存在")
        print(f"  📊 文件大小: {size} 字节")
        
        # 检查关键表名
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tables = [
            'document_classifications',
            'extraction_results',
            'toc_extraction_rules',
            'llm_validation_logs',
            'source_reliability_stats',
            'extraction_corrections',
            'processing_performance'
        ]
        
        for table in tables:
            if f'CREATE TABLE' in content and table in content:
                print(f"  ✅ 表 '{table}' 已定义")
            else:
                print(f"  ⚠️  表 '{table}' 未找到")
    else:
        print(f"  ❌ 文件不存在")
        all_ok = False
    
    # 总结
    print("\n" + "="*60)
    if all_ok:
        print("✅ 所有文件检查通过！")
        print("="*60)
        print("\n💡 下一步:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 初始化数据库: psql -h localhost -d bidding_db -f backend/database/document_processing_schema.sql")
        print("3. 运行测试: python3 backend/test_document_processing.py")
        print()
        return 0
    else:
        print("❌ 有文件检查失败")
        print("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
