#!/usr/bin/env python3
"""
预检查脚本：在安装前验证所有前置条件
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

class PreInstallCheck:
    """安装前检查"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_path = self.project_root / 'backend'
        self.issues = []
        self.warnings = []
    
    def check_python(self):
        """检查 Python 版本"""
        print("🐍 检查 Python...")
        version = sys.version_info
        
        if version >= (3, 8):
            print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            msg = f"Python 版本过低: {version.major}.{version.minor} (需要 3.8+)"
            print(f"  ❌ {msg}")
            self.issues.append(msg)
            return False
    
    def check_postgres(self):
        """检查 PostgreSQL"""
        print("🗄️  检查 PostgreSQL...")
        
        try:
            result = subprocess.run(
                ['psql', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"  ✅ {result.stdout.strip()}")
                
                # 尝试连接
                try:
                    import psycopg2
                    try:
                        conn = psycopg2.connect(
                            host='localhost',
                            port=5432,
                            user='postgres',
                            password='postgres'
                        )
                        conn.close()
                        print(f"  ✅ PostgreSQL 服务运行中 (localhost:5432)")
                        return True
                    except psycopg2.OperationalError as e:
                        msg = f"无法连接 PostgreSQL: {e}"
                        print(f"  ❌ {msg}")
                        self.issues.append(msg)
                        return False
                except ImportError:
                    print(f"  ⚠️  psycopg2 未安装，稍后会安装")
                    return True
            else:
                msg = "psql 命令失败"
                print(f"  ❌ {msg}")
                self.issues.append(msg)
                return False
                
        except FileNotFoundError:
            msg = "psql 未找到，请先安装 PostgreSQL"
            print(f"  ❌ {msg}")
            self.issues.append(msg)
            return False
        except Exception as e:
            msg = f"检查 PostgreSQL 时出错: {e}"
            print(f"  ⚠️  {msg}")
            self.warnings.append(msg)
            return True
    
    def check_directories(self):
        """检查目录权限"""
        print("📁 检查目录权限...")
        
        dirs_to_check = [
            self.project_root,
            self.backend_path,
        ]
        
        for d in dirs_to_check:
            if os.access(d, os.W_OK | os.X_OK):
                print(f"  ✅ {d.name}: 可读可写")
            else:
                msg = f"{d.name}: 权限不足"
                print(f"  ⚠️  {msg}")
                self.warnings.append(msg)
        
        return True
    
    def check_files(self):
        """检查关键文件是否存在"""
        print("📄 检查关键文件...")
        
        required_files = [
            'backend/init_database.sql',
            'backend/requirements.txt',
            'backend/core/config.py',
            'backend/routers/files.py',
        ]
        
        missing = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path}")
                missing.append(file_path)
        
        if missing:
            msg = f"缺失文件: {', '.join(missing)}"
            self.issues.append(msg)
            return False
        
        return True
    
    def check_existing_data(self):
        """检查是否存在现有数据"""
        print("💾 检查现有数据...")
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres',
                database='bidding_db'
            )
            cursor = conn.cursor()
            
            # 检查表数量
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema='public'
            """)
            table_count = cursor.fetchone()[0]
            
            # 检查数据量
            cursor.execute("SELECT COUNT(*) FROM uploaded_files")
            files_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM files")
            parsed_files_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"  📊 现有表: {table_count} 个")
            print(f"  📄 上传文件: {files_count} 个")
            print(f"  ✅ 解析文件: {parsed_files_count} 个")
            
            if table_count > 0:
                print(f"  ℹ️  数据库中已有数据，安装将自动迁移")
            
            return True
            
        except Exception as e:
            print(f"  ℹ️  数据库不存在或无法连接，安装时将创建")
            return True
    
    def check_config(self):
        """检查配置文件"""
        print("⚙️  检查配置...")
        
        config_file = self.backend_path / 'core' / 'config.py'
        env_file = self.backend_path / '.env'
        
        if config_file.exists():
            print(f"  ✅ config.py 存在")
        else:
            msg = f"config.py 缺失"
            print(f"  ❌ {msg}")
            self.issues.append(msg)
            return False
        
        if env_file.exists():
            print(f"  ✅ .env 存在")
        else:
            print(f"  ℹ️  .env 不存在，将使用默认配置")
        
        return True
    
    def run_all_checks(self):
        """运行所有检查"""
        print("=" * 60)
        print("📋 安装前预检查")
        print("=" * 60)
        print()
        
        checks = [
            ("Python 版本", self.check_python),
            ("PostgreSQL", self.check_postgres),
            ("关键文件", self.check_files),
            ("目录权限", self.check_directories),
            ("配置文件", self.check_config),
            ("现有数据", self.check_existing_data),
        ]
        
        for name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                print(f"  ❌ 检查 {name} 时出错: {e}")
                self.issues.append(f"{name} 检查失败: {e}")
            
            print()
        
        # 总结
        print("=" * 60)
        
        if not self.issues:
            print("✅ 所有检查通过！可以开始安装")
            print("=" * 60)
            
            if self.warnings:
                print("\n⚠️  有以下警告:")
                for w in self.warnings:
                    print(f"  • {w}")
            
            return 0
        else:
            print("❌ 有以下问题需要解决:")
            for issue in self.issues:
                print(f"  • {issue}")
            print("=" * 60)
            
            print("\n💡 建议:")
            if "PostgreSQL" in str(self.issues):
                print("  • 请安装和启动 PostgreSQL")
                print("  • macOS: brew install postgresql && brew services start postgresql")
                print("  • Linux: sudo apt-get install postgresql postgresql-contrib")
            
            if "Python" in str(self.issues):
                print("  • 请升级 Python 到 3.8 或更高版本")
            
            print()
            return 1

if __name__ == '__main__':
    checker = PreInstallCheck()
    sys.exit(checker.run_all_checks())
