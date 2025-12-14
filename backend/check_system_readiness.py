#!/usr/bin/env python3
"""
系统就绪检查脚本
验证文档处理系统所有依赖和配置是否就绪
"""

import sys
import os
from pathlib import Path
import subprocess
import importlib
import json
from datetime import datetime

class SystemReadinessCheck:
    """系统就绪性检查"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'status': 'unknown',
            'issues': []
        }
    
    def check_python_version(self):
        """检查 Python 版本"""
        version = sys.version_info
        result = {
            'name': 'Python 版本',
            'required': '3.8+',
            'actual': f'{version.major}.{version.minor}.{version.micro}',
            'passed': version >= (3, 8)
        }
        
        self.results['checks']['python_version'] = result
        if result['passed']:
            print(f"✅ Python 版本: {result['actual']}")
        else:
            print(f"❌ Python 版本: {result['actual']} (需要 {result['required']})")
            self.results['issues'].append('Python版本过低')
        
        return result['passed']
    
    def check_dependencies(self):
        """检查 Python 依赖"""
        dependencies = [
            'fastapi',
            'pydantic',
            'asyncio',
            'pypdf',
            'pdfplumber',
            'pillow',
            'paddlepaddle',
            'paddleocr',
            'psycopg2',
            'sqlalchemy',
            'openai'
        ]
        
        results = {}
        all_passed = True
        
        for dep in dependencies:
            try:
                mod = importlib.import_module(dep.replace('-', '_'))
                version = getattr(mod, '__version__', 'unknown')
                results[dep] = {
                    'installed': True,
                    'version': version
                }
                print(f"✅ {dep}: {version}")
            except ImportError:
                results[dep] = {
                    'installed': False,
                    'version': 'N/A'
                }
                print(f"❌ {dep}: 未安装")
                self.results['issues'].append(f'{dep} 未安装')
                all_passed = False
        
        self.results['checks']['dependencies'] = results
        return all_passed
    
    def check_directories(self):
        """检查目录结构"""
        backend_path = Path(__file__).parent / 'backend'
        required_dirs = [
            'backend',
            'backend/engines',
            'backend/routers',
            'backend/db',
            'backend/core',
            'backend/uploads',
            'backend/logs',
            'backend/documents'
        ]
        
        results = {}
        all_passed = True
        
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            exists = full_path.exists()
            results[dir_path] = {'exists': exists}
            
            if exists:
                print(f"✅ {dir_path}: 存在")
            else:
                print(f"⚠️  {dir_path}: 不存在 (将自动创建)")
                # 创建目录
                full_path.mkdir(parents=True, exist_ok=True)
        
        self.results['checks']['directories'] = results
        return True  # 目录不存在时自动创建，不算失败
    
    def check_modules(self):
        """检查新增模块"""
        backend_path = Path('backend')
        modules = [
            'backend/engines/smart_document_classifier.py',
            'backend/engines/ocr_extractor.py',
            'backend/engines/document_processor.py'
        ]
        
        results = {}
        all_passed = True
        
        for module_path in modules:
            full_path = Path(module_path)
            exists = full_path.exists()
            results[module_path] = {'exists': exists}
            
            if exists:
                # 检查文件大小
                size = full_path.stat().st_size
                print(f"✅ {module_path}: {size} 字节")
            else:
                print(f"❌ {module_path}: 不存在")
                self.results['issues'].append(f'{module_path} 文件缺失')
                all_passed = False
        
        self.results['checks']['modules'] = results
        return all_passed
    
    def check_database_schema(self):
        """检查数据库 schema 文件"""
        schema_file = Path('backend/database/document_processing_schema.sql')
        result = {
            'file': str(schema_file),
            'exists': schema_file.exists(),
            'size': schema_file.stat().st_size if schema_file.exists() else 0
        }
        
        if result['exists']:
            print(f"✅ 数据库 schema: {result['size']} 字节")
        else:
            print(f"❌ 数据库 schema 文件缺失")
            self.results['issues'].append('数据库schema文件缺失')
        
        self.results['checks']['database_schema'] = result
        return result['exists']
    
    def check_documentation(self):
        """检查文档"""
        docs = [
            'backend/FILE_PROCESSING_STRATEGY.md',
            'backend/IMPLEMENTATION_SUMMARY.md',
            'backend/INTEGRATION_GUIDE.md',
            'backend/test_document_processing.py'
        ]
        
        results = {}
        all_passed = True
        
        for doc in docs:
            doc_path = Path(doc)
            exists = doc_path.exists()
            results[doc] = {
                'exists': exists,
                'size': doc_path.stat().st_size if exists else 0
            }
            
            if exists:
                print(f"✅ {doc}: {results[doc]['size']} 字节")
            else:
                print(f"⚠️  {doc}: 不存在")
        
        self.results['checks']['documentation'] = results
        return True  # 文档不存在不算失败
    
    def check_configuration(self):
        """检查配置文件"""
        backend_path = Path('backend')
        config_files = [
            'backend/.env.example',
            'backend/core/config.py',
            'backend/requirements.txt'
        ]
        
        results = {}
        
        for config_file in config_files:
            config_path = Path(config_file)
            exists = config_path.exists()
            results[config_file] = {'exists': exists}
            
            if exists:
                print(f"✅ {config_file}: 存在")
            else:
                print(f"⚠️  {config_file}: 不存在")
        
        self.results['checks']['configuration'] = results
        return True
    
    def test_imports(self):
        """测试关键模块导入"""
        print("\n🔍 测试模块导入...")
        
        try:
            sys.path.insert(0, str(Path('backend').absolute()))
            
            try:
                from engines.smart_document_classifier import SmartDocumentClassifier
                print("✅ SmartDocumentClassifier 导入成功")
            except Exception as e:
                print(f"❌ SmartDocumentClassifier 导入失败: {e}")
                self.results['issues'].append(f'SmartDocumentClassifier导入失败: {e}')
                return False
            
            try:
                from engines.ocr_extractor import HybridTextExtractor
                print("✅ HybridTextExtractor 导入成功")
            except Exception as e:
                print(f"❌ HybridTextExtractor 导入失败: {e}")
                self.results['issues'].append(f'HybridTextExtractor导入失败: {e}')
                return False
            
            try:
                from engines.document_processor import DocumentProcessor
                print("✅ DocumentProcessor 导入成功")
            except Exception as e:
                print(f"❌ DocumentProcessor 导入失败: {e}")
                self.results['issues'].append(f'DocumentProcessor导入失败: {e}')
                return False
            
            return True
        
        except Exception as e:
            print(f"❌ 模块导入测试失败: {e}")
            self.results['issues'].append(f'模块导入失败: {e}')
            return False
    
    def run_all_checks(self):
        """运行所有检查"""
        print("=" * 60)
        print("🚀 文档处理系统就绪检查")
        print("=" * 60)
        
        checks = [
            ("Python 版本检查", self.check_python_version),
            ("依赖检查", self.check_dependencies),
            ("目录结构检查", self.check_directories),
            ("模块文件检查", self.check_modules),
            ("数据库 Schema 检查", self.check_database_schema),
            ("文档检查", self.check_documentation),
            ("配置检查", self.check_configuration),
            ("模块导入测试", self.test_imports)
        ]
        
        results = []
        for name, check_func in checks:
            print(f"\n📋 {name}...")
            try:
                result = check_func()
                results.append(result)
            except Exception as e:
                print(f"❌ {name} 异常: {e}")
                self.results['issues'].append(f'{name}异常: {e}')
                results.append(False)
        
        # 总体状态
        print("\n" + "=" * 60)
        if all(results):
            self.results['status'] = 'ready'
            print("✅ 系统已就绪！可以进行集成测试")
        else:
            self.results['status'] = 'not_ready'
            print("⚠️  系统还未完全就绪，请解决以下问题:")
            for issue in self.results['issues']:
                print(f"  • {issue}")
        print("=" * 60)
        
        # 保存检查结果
        report_path = Path('backend/READINESS_CHECK_REPORT.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 检查报告已保存到: {report_path}")
        
        return self.results['status'] == 'ready'


if __name__ == '__main__':
    checker = SystemReadinessCheck()
    is_ready = checker.run_all_checks()
    
    sys.exit(0 if is_ready else 1)
