#!/usr/bin/env python3
"""
真实文档验证脚本 - 验证Skills的准确性和性能

验证策略：
1. 使用pdfplumber直接提取 vs TableExtractor Skill
2. 使用PyMuPDF直接提取 vs ImageProcessor Skill  
3. 对比提取数量、处理时间、输出质量

使用方法：
    python validate_skills_production.py --file path/to/file.pdf
    python validate_skills_production.py --batch uploads/
"""

import sys
import time
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import traceback

# 确保可以导入backend模块
sys.path.insert(0, str(Path(__file__).parent))

# 原始库
try:
    import pdfplumber
    import fitz  # PyMuPDF
    HAS_PDF_LIBS = True
except ImportError:
    HAS_PDF_LIBS = False
    print("⚠️  pdfplumber或PyMuPDF未安装，仅能测试Skills")

# New Skills
from skills.table_extractor import TableExtractor, TableExtractorInput
from skills.image_processor import ImageProcessor, ImageProcessorInput


@dataclass
class ValidationResult:
    """单个文件的验证结果"""
    file_path: str
    file_type: str  # pdf, docx
    
    # Legacy实现结果
    legacy_time: float
    legacy_tables: int
    legacy_images: int
    
    # Skills实现结果
    skills_time: float
    skills_tables: int
    skills_images: int
    
    # Optional错误信息
    legacy_error: Optional[str] = None
    skills_error: Optional[str] = None
    
    # 对比分析（自动计算）
    time_improvement: float = 0.0  # 负值表示变慢
    table_diff: int = 0
    image_diff: int = 0
    consistency_check: str = "PASS"  # PASS, FAIL, WARNING
    
    def __post_init__(self):
        """计算对比指标"""
        if self.legacy_time > 0:
            self.time_improvement = ((self.legacy_time - self.skills_time) / self.legacy_time) * 100
        
        self.table_diff = self.skills_tables - self.legacy_tables
        self.image_diff = self.skills_images - self.legacy_images
        
        # 一致性检查
        if abs(self.table_diff) > 2 or abs(self.image_diff) > 2:
            self.consistency_check = "WARNING"
        if self.legacy_error or self.skills_error:
            self.consistency_check = "FAIL"


class ProductionValidator:
    """生产环境验证器 - 对比原始库和Skills"""
    
    def __init__(self, output_dir: str = "validation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化新Skills
        print("🔧 初始化Skills...")
        self.skill_table = TableExtractor()
        self.skill_image = ImageProcessor()
        
        self.results: List[ValidationResult] = []
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """验证单个文件"""
        file_path = Path(file_path).resolve()
        
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        print(f"\n{'='*60}")
        print(f"📄 验证文件: {file_path.name}")
        print(f"   大小: {file_path.stat().st_size / 1024:.1f} KB")
        print(f"{'='*60}")
        
        file_type = file_path.suffix.lower().replace('.', '')
        file_id = hashlib.md5(file_path.name.encode()).hexdigest()[:8]
        
        # ===== 原始库测试 (作为基准) =====
        print("\n🔵 [Raw] 使用原始库提取 (基准)...")
        legacy_start = time.time()
        legacy_tables, legacy_images = 0, 0
        legacy_error = None
        
        try:
            if file_type == 'pdf' and HAS_PDF_LIBS:
                # pdfplumber提取表格
                with pdfplumber.open(str(file_path)) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        if tables:
                            legacy_tables += len(tables)
                
                # PyMuPDF提取图片
                doc = fitz.open(str(file_path))
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    images = page.get_images()
                    legacy_images += len(images)
                doc.close()
                
                print(f"  ✅ 提取: {legacy_tables} 表格, {legacy_images} 图片")
            else:
                legacy_error = "DOCX或缺少库"
                print(f"  ⚠️  跳过原始库测试")
                
        except Exception as e:
            legacy_error = str(e)[:100]
            print(f"  ❌ 错误: {legacy_error}")
        
        legacy_time = time.time() - legacy_start
        print(f"  ⏱️  耗时: {legacy_time:.3f}s")
        
        # ===== Skills实现测试 =====
        print("\n🟢 [Skills] 使用Skill提取...")
        skills_start = time.time()
        skills_tables, skills_images = 0, 0
        skills_error = None
        
        try:
            # 表格提取
            table_input = TableExtractorInput(
                file_path=str(file_path),
                file_id=file_id
            )
            table_result = self.skill_table.execute(table_input)
            skills_tables = table_result.table_count
            print(f"  📊 TableExtractor: {skills_tables} 表格")
            
            # 图片提取
            image_input = ImageProcessorInput(
                file_path=str(file_path),
                file_id=file_id,
                year=2024,
                storage_base=str(self.output_dir / "images")
            )
            image_result = self.skill_image.execute(image_input)
            skills_images = image_result.image_count
            print(f"  🖼️  ImageProcessor: {skills_images} 图片")
            
        except Exception as e:
            skills_error = str(e)[:100]
            print(f"  ❌ 错误: {skills_error}")
            traceback.print_exc()
        
        skills_time = time.time() - skills_start
        print(f"  ⏱️  耗时: {skills_time:.3f}s")
        
        # ===== 生成验证结果 =====
        result = ValidationResult(
            file_path=str(file_path),
            file_type=file_type,
            legacy_time=legacy_time,
            legacy_tables=legacy_tables,
            legacy_images=legacy_images,
            legacy_error=legacy_error,
            skills_time=skills_time,
            skills_tables=skills_tables,
            skills_images=skills_images,
            skills_error=skills_error
        )
        
        # ===== 打印对比分析 =====
        print(f"\n📊 对比分析:")
        print(f"  性能: {result.time_improvement:+.1f}% {'🚀' if result.time_improvement > 0 else '🐌'}")
        print(f"  表格差异: {result.table_diff:+d} {'⚠️' if abs(result.table_diff) > 2 else '✅'}")
        print(f"  图片差异: {result.image_diff:+d} {'⚠️' if abs(result.image_diff) > 2 else '✅'}")
        print(f"  一致性: {result.consistency_check}")
        
        self.results.append(result)
        return result
    
    def validate_directory(self, dir_path: str, pattern: str = "*.pdf") -> List[ValidationResult]:
        """批量验证目录中的文件"""
        dir_path = Path(dir_path)
        files = list(dir_path.glob(pattern))
        
        print(f"\n🗂️  批量验证: {len(files)} 个文件 (模式: {pattern})")
        
        for file in files:
            self.validate_file(str(file))
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        if not self.results:
            print("⚠️  没有验证结果，跳过报告生成")
            return {
                "error": "没有验证结果", 
                "summary": {
                    "total_files": 0, 
                    "passed": 0, 
                    "warnings": 0, 
                    "failed": 0, 
                    "pass_rate": "0.0%"
                }, 
                "performance": {
                    "avg_legacy_time": "0.000s", 
                    "avg_skills_time": "0.000s", 
                    "avg_improvement": "0.0%"
                }, 
                "details": []
            }
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.consistency_check == "PASS")
        warnings = sum(1 for r in self.results if r.consistency_check == "WARNING")
        failed = sum(1 for r in self.results if r.consistency_check == "FAIL")
        
        avg_time_improvement = sum(r.time_improvement for r in self.results) / total
        avg_legacy_time = sum(r.legacy_time for r in self.results) / total
        avg_skills_time = sum(r.skills_time for r in self.results) / total
        
        report = {
            "summary": {
                "total_files": total,
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "pass_rate": f"{(passed/total)*100:.1f}%"
            },
            "performance": {
                "avg_legacy_time": f"{avg_legacy_time:.3f}s",
                "avg_skills_time": f"{avg_skills_time:.3f}s",
                "avg_improvement": f"{avg_time_improvement:+.1f}%"
            },
            "details": [asdict(r) for r in self.results]
        }
        
        # 保存JSON报告
        report_path = self.output_dir / f"validation_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 报告已保存: {report_path}")
        return report
    
    def print_summary(self):
        """打印汇总信息"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("📊 验证汇总报告")
        print("="*60)
        
        summary = report['summary']
        print(f"\n📈 测试结果:")
        print(f"  总文件数: {summary['total_files']}")
        print(f"  ✅ PASS:    {summary['passed']}")
        print(f"  ⚠️  WARNING: {summary['warnings']}")
        print(f"  ❌ FAIL:    {summary['failed']}")
        print(f"  通过率:    {summary['pass_rate']}")
        
        perf = report['performance']
        print(f"\n⚡ 性能对比:")
        print(f"  Legacy平均: {perf['avg_legacy_time']}")
        print(f"  Skills平均: {perf['avg_skills_time']}")
        print(f"  平均提升:   {perf['avg_improvement']}")
        
        # 识别问题文件
        problem_files = [r for r in self.results if r.consistency_check != "PASS"]
        if problem_files:
            print(f"\n⚠️  需要关注的文件:")
            for r in problem_files:
                print(f"  - {Path(r.file_path).name}: {r.consistency_check}")
                if r.legacy_error:
                    print(f"    Legacy错误: {r.legacy_error[:50]}")
                if r.skills_error:
                    print(f"    Skills错误: {r.skills_error[:50]}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="验证Skills生产就绪性")
    parser.add_argument('--file', type=str, help='验证单个文件')
    parser.add_argument('--batch', type=str, help='批量验证目录')
    parser.add_argument('--pattern', type=str, default='*.pdf', help='文件匹配模式 (默认: *.pdf)')
    parser.add_argument('--output', type=str, default='validation_results', help='输出目录')
    
    args = parser.parse_args()
    
    validator = ProductionValidator(output_dir=args.output)
    
    if args.file:
        # 单文件验证
        validator.validate_file(args.file)
    elif args.batch:
        # 批量验证
        validator.validate_directory(args.batch, pattern=args.pattern)
    else:
        # 默认：验证uploads/目录
        print("未指定文件，使用默认uploads/目录...")
        validator.validate_directory('uploads', pattern='*.pdf')
        validator.validate_directory('uploads', pattern='*.docx')
    
    validator.print_summary()


if __name__ == '__main__':
    main()
