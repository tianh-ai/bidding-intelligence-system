#!/usr/bin/env python3
"""
测试财务报告分离功能
"""
import sys
sys.path.insert(0, '/app')

from engines.financial_report_splitter import FinancialReportSplitter
from core.logger import logger

def test_splitter():
    """测试财务报告分离器"""
    
    print("="*60)
    print("财务报告分离器测试")
    print("="*60)
    
    # 初始化
    splitter = FinancialReportSplitter()
    print(f"\n✅ 初始化成功")
    print(f"   存储目录: {splitter.financial_dir}")
    
    # 测试年份提取
    test_texts = [
        "2023年度财务报表",
        "截至2022年12月31日",
        "审计报告 2021年",
        "财务报表2020",
    ]
    
    print(f"\n📝 测试年份提取:")
    for text in test_texts:
        year = splitter._extract_year_from_text(text)
        print(f"   '{text}' → {year}年")
    
    # 查找测试文件
    print(f"\n📁 查找财务报告PDF文件...")
    import os
    from pathlib import Path
    
    archive_dir = Path("/Volumes/ssd/bidding-data/archive")
    pdf_files = list(archive_dir.rglob("*.pdf"))
    
    if pdf_files:
        print(f"   找到{len(pdf_files)}个PDF文件:")
        for i, pdf in enumerate(pdf_files[:5], 1):
            size_mb = pdf.stat().st_size / (1024*1024)
            print(f"   {i}. {pdf.name} ({size_mb:.1f}MB)")
        
        # 如果有包含"财务"或"审计"的文件，测试分离
        financial_pdfs = [p for p in pdf_files if any(kw in p.name for kw in ['财务', '审计', '年报'])]
        if financial_pdfs:
            test_pdf = financial_pdfs[0]
            print(f"\n🧪 测试分离文件: {test_pdf.name}")
            
            file_id = "test-" + str(hash(test_pdf.name))[:8]
            result = splitter.split_and_archive(str(test_pdf), file_id)
            
            print(f"\n✅ 分离完成:")
            for item in result:
                print(f"   {item['year']}年: {item['page_count']}页, {item['file_size']//1024}KB")
                print(f"   路径: {item['archive_path']}")
        else:
            print(f"   ⚠️ 未找到财务报告PDF文件")
    else:
        print(f"   ⚠️ 未找到任何PDF文件")
    
    print(f"\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == '__main__':
    test_splitter()
