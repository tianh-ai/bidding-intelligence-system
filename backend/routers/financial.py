"""
财务报告API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Optional
from pathlib import Path
import uuid

from engines.financial_report_splitter import FinancialReportSplitter
from core.logger import logger
from database import db

router = APIRouter(prefix="/financial", tags=["财务报告"])


@router.post("/split-report")
async def split_financial_report(file_id: str):
    """
    分离财务报告按年份
    
    Args:
        file_id: 已上传文件的ID
        
    Returns:
        {
            'status': 'success',
            'archived_files': [
                {
                    'year': 2023,
                    'archive_path': '...',
                    'page_count': 15,
                    'file_size': 1234567
                },
                ...
            ]
        }
    """
    try:
        # 查询文件路径
        result = db.query_one(
            "SELECT archive_path FROM uploaded_files WHERE id = %s",
            (file_id,)
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = result['archive_path']
        
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="文件物理路径不存在")
        
        # 执行分离
        splitter = FinancialReportSplitter()
        archived_files = splitter.split_and_archive(file_path, file_id)
        
        if not archived_files:
            raise HTTPException(status_code=500, detail="分离失败")
        
        return {
            'status': 'success',
            'file_id': file_id,
            'archived_files': archived_files,
            'total_files': len(archived_files),
            'years': [f['year'] for f in archived_files if f.get('year')]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分离财务报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/archived-reports/{file_id}")
async def get_archived_reports(file_id: str):
    """
    获取已存档的财务报告列表
    
    Returns:
        [
            {
                'year': 2023,
                'archive_path': '...',
                'page_count': 15,
                'file_size': 1234567,
                'archived_at': '2025-12-14 10:30:00'
            },
            ...
        ]
    """
    try:
        splitter = FinancialReportSplitter()
        reports = splitter.get_archived_reports(file_id)
        
        return {
            'status': 'success',
            'file_id': file_id,
            'reports': reports,
            'total': len(reports)
        }
        
    except Exception as e:
        logger.error(f"查询存档报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports-by-year/{year}")
async def get_reports_by_year(year: int):
    """
    获取指定年份的所有财务报告
    
    Args:
        year: 年份 (如 2023)
        
    Returns:
        [
            {
                'file_id': 'xxx',
                'archive_path': '...',
                'page_count': 15,
                'file_size': 1234567,
                'archived_at': '...'
            },
            ...
        ]
    """
    try:
        result = db.query_all("""
            SELECT 
                fr.file_id,
                fr.archive_path,
                fr.page_count,
                fr.file_size,
                fr.archived_at,
                uf.filename as original_filename
            FROM financial_reports fr
            LEFT JOIN uploaded_files uf ON fr.file_id = uf.id
            WHERE fr.year = %s
            ORDER BY fr.archived_at DESC
        """, (year,))
        
        reports = [dict(row) for row in result] if result else []
        
        return {
            'status': 'success',
            'year': year,
            'reports': reports,
            'total': len(reports)
        }
        
    except Exception as e:
        logger.error(f"查询年度报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/years")
async def get_available_years():
    """
    获取所有有财务报告的年份
    
    Returns:
        {
            'years': [2023, 2022, 2021, ...],
            'report_counts': {2023: 5, 2022: 3, ...}
        }
    """
    try:
        result = db.query_all("""
            SELECT 
                year,
                COUNT(*) as report_count
            FROM financial_reports
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
        """)
        
        years = [row['year'] for row in result] if result else []
        counts = {row['year']: row['report_count'] for row in result} if result else {}
        
        return {
            'status': 'success',
            'years': years,
            'report_counts': counts,
            'total_years': len(years)
        }
        
    except Exception as e:
        logger.error(f"查询年份列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
