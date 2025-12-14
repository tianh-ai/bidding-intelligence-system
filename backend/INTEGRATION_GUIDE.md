#!/usr/bin/env python3
"""
集成指南: 如何将新的文档处理系统集成到现有的文件上传路由

这个文件提供了完整的集成步骤和代码示例
"""

# =====================================================
# 第 1 步: 在 routers/files.py 中导入新模块
# =====================================================

IMPORT_SECTION = """
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import asyncio
from pathlib import Path
from datetime import datetime

# 新增导入
from engines.document_processor import DocumentProcessor
from engines.smart_document_classifier import DocumentType
from db.ontology import OntologyDB  # 用于存储分类结果
"""

# =====================================================
# 第 2 步: 修改上传端点
# =====================================================

MODIFIED_UPLOAD_ENDPOINT = """
@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    '''
    改进的文件上传端点，集成文档分类和处理
    
    流程:
    1. 保存文件
    2. 分类文件类型和处理策略
    3. 根据类型进行相应处理
    4. 保存分类结果到数据库
    5. 返回结果
    '''
    
    processor = DocumentProcessor()
    ontology_db = OntologyDB()  # 获取数据库连接
    results = []
    
    try:
        for file in files:
            file_path = None
            file_id = None
            
            try:
                # 1. 保存上传的文件到临时位置
                upload_dir = Path("backend/uploads")
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / file.filename
                
                with open(file_path, 'wb') as f:
                    f.write(await file.read())
                
                logger.info(f"📁 文件已保存: {file_path}")
                
                # 2. 在数据库中记录文件
                file_id = await ontology_db.save_uploaded_file(
                    filename=file.filename,
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    upload_timestamp=datetime.now()
                )
                
                # 3. 文档分类和处理
                logger.info(f"⚙️  处理文件: {file.filename}")
                processing_result = await processor.process(
                    file_path=str(file_path),
                    filename=file.filename
                )
                
                # 4. 保存分类结果到数据库
                if processing_result['status'] == 'success':
                    classification_id = await ontology_db.save_document_classification(
                        file_id=file_id,
                        classification_data=processing_result['classification'],
                        processing_strategy=processing_result['processing_strategy'],
                        total_pages=processing_result['total_pages']
                    )
                    
                    # 5. 根据文件类型进行后续处理
                    file_type = processing_result['file_type']
                    
                    if file_type == 'main_proposal':
                        # ✅ 主标书: 提取章节并保存到知识库
                        chapters = processing_result.get('chapters', [])
                        for chapter in chapters:
                            await ontology_db.save_chapter(
                                file_id=file_id,
                                chapter_data=chapter
                            )
                        logger.info(f"  ✅ 提取并保存 {len(chapters)} 个章节")
                    
                    elif file_type == 'financial_report':
                        # 💼 财务报告: 按年份分类保存
                        detected_years = processing_result['classification'].get('financial_years', [])
                        for year in detected_years:
                            year_dir = Path(f"backend/documents/financial_reports/{year}")
                            year_dir.mkdir(parents=True, exist_ok=True)
                            year_file = year_dir / file.filename
                            file_path.rename(year_file)
                            logger.info(f"  💼 财务报告 {year}: {year_file}")
                    
                    elif file_type in ['license', 'certificate', 'performance_report', 'audit_report']:
                        # 📄 证件/报告: 仅保存，记录元数据
                        cert_dir = Path(f"backend/documents/{file_type}s")
                        cert_dir.mkdir(parents=True, exist_ok=True)
                        cert_file = cert_dir / file.filename
                        file_path.rename(cert_file)
                        logger.info(f"  📄 {file_type} 已保存: {cert_file}")
                    
                    elif file_type == 'scan_pdf':
                        # 🔍 扫描PDF: 使用 OCR 提取文本
                        scan_dir = Path("backend/documents/scans")
                        scan_dir.mkdir(parents=True, exist_ok=True)
                        scan_file = scan_dir / file.filename
                        file_path.rename(scan_file)
                        logger.info(f"  🔍 扫描文件: {scan_file}")
                    
                    result = {
                        'filename': file.filename,
                        'status': 'success',
                        'file_type': file_type,
                        'classification_id': classification_id,
                        'chapters_count': len(processing_result.get('chapters', [])),
                        'total_pages': processing_result['total_pages'],
                        'message': f'文件处理成功: {file_type}'
                    }
                else:
                    result = {
                        'filename': file.filename,
                        'status': 'error',
                        'message': processing_result.get('error', '处理失败'),
                        'error_detail': processing_result.get('error_detail')
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"❌ 处理文件失败: {e}", exc_info=True)
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(e)
                })
        
        return {
            'status': 'success',
            'message': f'处理完成: {len(results)} 个文件',
            'results': results
        }
    
    except Exception as e:
        logger.error(f"❌ 上传处理错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
"""

# =====================================================
# 第 3 步: 添加数据库辅助方法
# =====================================================

DATABASE_HELPER_METHODS = """
# 在 db/ontology.py 中添加以下方法

class OntologyDB:
    
    async def save_uploaded_file(self, filename: str, file_path: str, 
                                  file_size: int, upload_timestamp):
        '''保存上传的文件信息'''
        query = '''
            INSERT INTO uploaded_files (filename, file_path, file_size, upload_timestamp)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        '''
        return await self.db.fetchval(query, filename, file_path, file_size, upload_timestamp)
    
    async def save_document_classification(self, file_id: int, 
                                          classification_data: dict,
                                          processing_strategy: str,
                                          total_pages: int):
        '''保存文档分类结果'''
        query = '''
            INSERT INTO document_classifications 
            (file_id, file_type, processing_strategy, total_pages, 
             text_page_ratio, scan_page_ratio, is_financial_report, 
             is_certificate, detected_years)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        '''
        
        clf = classification_data
        return await self.db.fetchval(
            query,
            file_id,
            clf.get('file_type'),
            processing_strategy,
            total_pages,
            clf.get('text_page_ratio', 0.0),
            clf.get('scan_page_ratio', 0.0),
            clf.get('is_financial_report', False),
            clf.get('is_certificate', False),
            clf.get('detected_years', [])
        )
    
    async def save_chapter(self, file_id: int, chapter_data: dict):
        '''保存提取的章节'''
        query = '''
            INSERT INTO chapters (file_id, level, title, content)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        '''
        
        return await self.db.fetchval(
            query,
            file_id,
            chapter_data.get('level'),
            chapter_data.get('title'),
            chapter_data.get('content')
        )
"""

# =====================================================
# 第 4 步: 测试集成
# =====================================================

INTEGRATION_TEST = """
# test_integrated_upload.py

import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_upload_main_proposal():
    '''测试上传主标书'''
    with open('test_files/标书.pdf', 'rb') as f:
        response = client.post(
            '/api/files/upload',
            files=('file', f)
        )
    
    assert response.status_code == 200
    result = response.json()
    assert result['results'][0]['status'] == 'success'
    assert result['results'][0]['file_type'] == 'main_proposal'
    print(f"✅ 提取章节: {result['results'][0]['chapters_count']}")

def test_upload_financial_report():
    '''测试上传财务报告'''
    with open('test_files/财务报告.pdf', 'rb') as f:
        response = client.post(
            '/api/files/upload',
            files=('file', f)
        )
    
    assert response.status_code == 200
    result = response.json()
    assert result['results'][0]['status'] == 'success'
    assert result['results'][0]['file_type'] == 'financial_report'
    print(f"✅ 检测年份: {result['results'][0].get('detected_years')}")

def test_upload_certificate():
    '''测试上传证件'''
    with open('test_files/营业执照.pdf', 'rb') as f:
        response = client.post(
            '/api/files/upload',
            files=('file', f)
        )
    
    assert response.status_code == 200
    result = response.json()
    assert result['results'][0]['status'] == 'success'
    assert result['results'][0]['file_type'] == 'license'
    print("✅ 证件已保存（仅存储，不解析）")

if __name__ == '__main__':
    print("🧪 开始集成测试")
    test_upload_main_proposal()
    test_upload_financial_report()
    test_upload_certificate()
    print("✅ 所有测试通过！")
"""

# =====================================================
# 第 5 步: 部署检查清单
# =====================================================

DEPLOYMENT_CHECKLIST = """
部署前检查清单:

[ ] 1. 数据库模式已应用
    - 运行: psql -h localhost -d bidding_db -f backend/database/document_processing_schema.sql
    - 确保所有表都创建成功

[ ] 2. 依赖已安装
    - 运行: pip install -r backend/requirements.txt
    - 确保 paddlepaddle, paddleocr, pillow 已安装

[ ] 3. 存储目录已创建
    - backend/uploads/
    - backend/documents/financial_reports/
    - backend/documents/licenses/
    - backend/documents/certificates/
    - backend/documents/performance_reports/
    - backend/documents/scans/

[ ] 4. 环境变量已配置
    - .env 中包含 OPENAI_API_KEY
    - 数据库连接参数正确

[ ] 5. 日志已配置
    - backend/logs/ 目录存在
    - 日志级别设置为 INFO 或 DEBUG

[ ] 6. 测试已通过
    - python backend/test_document_processing.py
    - 所有测试应该通过

[ ] 7. 前端已准备
    - 前端能接收新的 file_type 字段
    - UI 能显示分类结果

[ ] 8. 备份已完成
    - 备份现有数据库
    - 备份现有上传目录

部署命令:
1. 启动后端: python backend/main.py
2. 启动 Worker: celery -A backend.worker worker
3. 启动前端: npm run dev (前端目录)
"""

# =====================================================
# 第 6 步: 性能监控
# =====================================================

PERFORMANCE_MONITORING = """
性能监控查询:

# 查看最近处理的文件
SELECT 
    f.filename,
    dc.file_type,
    pp.total_time_ms,
    pp.total_pages,
    ROUND(pp.total_time_ms::float / pp.total_pages, 2) as ms_per_page
FROM document_classifications dc
JOIN uploaded_files f ON dc.file_id = f.id
JOIN processing_performance pp ON dc.id = pp.document_classification_id
ORDER BY pp.created_at DESC
LIMIT 10;

# 统计各文件类型的处理时间
SELECT 
    file_type,
    COUNT(*) as file_count,
    ROUND(AVG(total_time_ms)) as avg_time_ms,
    MAX(total_time_ms) as max_time_ms,
    ROUND(AVG(total_pages)) as avg_pages
FROM processing_performance
GROUP BY file_type
ORDER BY avg_time_ms DESC;

# 查看 OCR 使用率
SELECT 
    CASE WHEN scan_page_ratio > 0.5 THEN 'high_ocr'
         WHEN scan_page_ratio > 0.2 THEN 'mixed_ocr'
         ELSE 'text_only'
    END as ocr_usage,
    COUNT(*) as file_count,
    ROUND(AVG(scan_page_ratio), 2) as avg_scan_ratio
FROM document_classifications
GROUP BY ocr_usage;

# 检查提取方法的准确率
SELECT 
    extraction_method,
    COUNT(*) as total,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    COUNT(*) FILTER (WHERE confidence_score > 0.8) as high_confidence
FROM extraction_results
GROUP BY extraction_method;
"""

if __name__ == '__main__':
    print("📚 集成指南已生成")
    print("请按顺序参考各个部分进行集成")
