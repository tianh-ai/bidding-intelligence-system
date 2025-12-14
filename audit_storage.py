#!/usr/bin/env python3
"""
安装前数据存储验证脚本
检查文件系统、数据库、数据一致性
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

class StorageAudit:
    """数据存储审计"""
    
    def __init__(self):
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'issues': [],
            'status': 'pending'
        }
        self.backend_path = Path(__file__).parent / 'backend'
    
    def check_file_system(self):
        """检查文件系统"""
        print("\n📁 检查文件系统...")
        
        # 获取配置
        sys.path.insert(0, str(self.backend_path))
        try:
            from core.config import get_settings
            settings = get_settings()
            upload_path = settings.upload_path
            print(f"  ✅ 上传目录: {upload_path}")
        except Exception as e:
            print(f"  ❌ 无法获取配置: {e}")
            return False
        
        # 检查目录结构
        required_dirs = {
            'temp': os.path.join(upload_path, 'temp'),
            'parsed': os.path.join(upload_path, 'parsed'),
            'archive': os.path.join(upload_path, 'archive'),
        }
        
        for name, path in required_dirs.items():
            if os.path.exists(path):
                print(f"  ✅ {name}: {path}")
            else:
                print(f"  ⚠️  {name}: {path} (不存在，将自动创建)")
        
        self.report['checks']['file_system'] = {
            'upload_path': upload_path,
            'dirs': required_dirs,
            'writable': os.access(upload_path, os.W_OK)
        }
        
        return True
    
    def check_database(self):
        """检查数据库"""
        print("\n🗄️  检查数据库...")
        
        sys.path.insert(0, str(self.backend_path))
        try:
            from core.config import get_settings
            settings = get_settings()
            
            # 检查数据库连接
            print(f"  📍 数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
            
            # 尝试连接
            import psycopg2
            try:
                conn = psycopg2.connect(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    database=settings.DB_NAME
                )
                cursor = conn.cursor()
                
                # 检查关键表
                tables_to_check = [
                    'uploaded_files',
                    'files',
                    'chapters',
                    'vectors',
                    'chapter_structure_rules',
                    'chapter_content_rules',
                ]
                
                existing_tables = []
                missing_tables = []
                
                for table in tables_to_check:
                    cursor.execute(f"""
                        SELECT EXISTS(
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        )
                    """)
                    if cursor.fetchone()[0]:
                        existing_tables.append(table)
                        print(f"  ✅ {table}")
                    else:
                        missing_tables.append(table)
                        print(f"  ❌ {table} (缺失)")
                
                cursor.close()
                conn.close()
                
                self.report['checks']['database'] = {
                    'host': settings.DB_HOST,
                    'port': settings.DB_PORT,
                    'database': settings.DB_NAME,
                    'existing_tables': existing_tables,
                    'missing_tables': missing_tables,
                    'status': '✅ 连接成功' if not missing_tables else '⚠️  某些表缺失'
                }
                
                return len(missing_tables) == 0
                
            except psycopg2.OperationalError as e:
                print(f"  ❌ 数据库连接失败: {e}")
                print(f"     请确保 PostgreSQL 运行在 {settings.DB_HOST}:{settings.DB_PORT}")
                self.report['issues'].append(f'数据库连接失败: {e}')
                return False
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            self.report['issues'].append(str(e))
            return False
    
    def check_data_consistency(self):
        """检查数据一致性"""
        print("\n🔗 检查数据一致性...")
        
        sys.path.insert(0, str(self.backend_path))
        try:
            from database import db
            
            # 检查孤立记录
            orphaned_checks = [
                {
                    'name': '孤立的章节',
                    'query': """
                        SELECT COUNT(*) FROM chapters c
                        WHERE NOT EXISTS(SELECT 1 FROM files f WHERE f.id = c.file_id)
                    """
                },
                {
                    'name': '孤立的向量',
                    'query': """
                        SELECT COUNT(*) FROM vectors v
                        WHERE NOT EXISTS(SELECT 1 FROM files f WHERE f.id = v.file_id)
                    """
                },
                {
                    'name': '孤立的规则',
                    'query': """
                        SELECT COUNT(*) FROM chapter_structure_rules r
                        WHERE NOT EXISTS(SELECT 1 FROM chapters c WHERE c.id = r.chapter_id)
                    """
                }
            ]
            
            consistency_ok = True
            for check in orphaned_checks:
                result = db.execute(check['query']).fetchone()
                count = result[0] if result else 0
                
                if count > 0:
                    print(f"  ⚠️  {check['name']}: {count} 条孤立记录")
                    self.report['issues'].append(f"{check['name']}: {count} 条孤立记录")
                    consistency_ok = False
                else:
                    print(f"  ✅ {check['name']}: 无孤立记录")
            
            self.report['checks']['data_consistency'] = {'status': '✅ 一致' if consistency_ok else '⚠️  有问题'}
            return consistency_ok
            
        except Exception as e:
            print(f"  ⚠️  无法检查数据一致性: {e}")
            return True  # 不中断流程
    
    def check_config(self):
        """检查配置"""
        print("\n⚙️  检查配置...")
        
        sys.path.insert(0, str(self.backend_path))
        try:
            from core.config import get_settings
            settings = get_settings()
            
            required_configs = [
                ('UPLOAD_DIR', settings.UPLOAD_DIR),
                ('DB_HOST', settings.DB_HOST),
                ('DB_PORT', settings.DB_PORT),
                ('DB_NAME', settings.DB_NAME),
                ('DB_USER', settings.DB_USER),
            ]
            
            for name, value in required_configs:
                if value:
                    print(f"  ✅ {name}: {value}")
                else:
                    print(f"  ❌ {name}: 未配置")
                    self.report['issues'].append(f'{name} 未配置')
                    return False
            
            self.report['checks']['config'] = {
                'upload_dir': settings.UPLOAD_DIR,
                'db_host': settings.DB_HOST,
                'db_port': settings.DB_PORT,
                'db_name': settings.DB_NAME
            }
            
            return True
            
        except Exception as e:
            print(f"  ❌ 配置检查失败: {e}")
            return False
    
    def run_full_audit(self):
        """运行完整审计"""
        print("=" * 60)
        print("📊 数据存储架构审计")
        print("=" * 60)
        
        checks = [
            ("配置检查", self.check_config),
            ("文件系统检查", self.check_file_system),
            ("数据库检查", self.check_database),
            ("数据一致性检查", self.check_data_consistency),
        ]
        
        results = []
        for name, check_func in checks:
            try:
                result = check_func()
                results.append(result)
            except Exception as e:
                print(f"❌ {name} 异常: {e}")
                results.append(False)
        
        # 总结
        print("\n" + "=" * 60)
        
        if all(results):
            self.report['status'] = '✅ 可以开始安装'
            print("✅ 所有检查通过！可以开始安装")
        else:
            self.report['status'] = '⚠️  有问题需要解决'
            print("⚠️  有以下问题需要解决:")
            for issue in self.report['issues']:
                print(f"  • {issue}")
        
        print("=" * 60)
        
        # 保存报告
        report_file = Path(__file__).parent / 'STORAGE_AUDIT_REPORT.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 审计报告: {report_file}")
        
        return all(results)

if __name__ == '__main__':
    auditor = StorageAudit()
    success = auditor.run_full_audit()
    sys.exit(0 if success else 1)
