"""
财务报告分离和存档引擎
将多年财务报告按年份分离为独立文件并存档
"""

import re
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pypdf import PdfReader, PdfWriter

from core.logger import logger
from database import db


class FinancialReportSplitter:
    """财务报告分离器"""
    
    # 年份识别模式
    YEAR_PATTERNS = [
        r'(\d{4})\s*年度?\s*(?:财务报表|审计报告|年报)',
        r'(?:财务报表|审计报告|年报).*?(\d{4})\s*年',
        r'截至\s*(\d{4})\s*年',
        r'(\d{4})\s*年\s*\d+\s*月\s*\d+\s*日',
    ]
    
    def __init__(self, storage_base: str = "/Volumes/ssd/bidding-data/archive"):
        self.storage_base = Path(storage_base)
        self.financial_dir = self.storage_base / "financial_reports"
        self.financial_dir.mkdir(parents=True, exist_ok=True)
    
    def split_and_archive(self, file_path: str, file_id: str) -> List[Dict]:
        """
        分离并存档财务报告
        
        Args:
            file_path: 源PDF文件路径
            file_id: 文件ID
            
        Returns:
            List[Dict]: 各年份报告信息
            [
                {
                    'year': 2023,
                    'pages': [0, 1, 2, ...],
                    'archive_path': '/path/to/2023_financial_report.pdf',
                    'page_count': 15
                },
                ...
            ]
        """
        logger.info(f"开始分离财务报告: {file_path}")
        
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            
            # 1. 识别年份分布
            year_ranges = self._detect_year_ranges(reader)
            
            if not year_ranges:
                logger.warning(f"未检测到年份，保存为单个文件")
                return self._save_as_single_file(file_path, file_id, total_pages)
            
            # 2. 按年份分离并保存
            archived_files = []
            for year_info in year_ranges:
                archived = self._save_year_report(
                    reader=reader,
                    year=year_info['year'],
                    pages=year_info['pages'],
                    file_id=file_id,
                    original_filename=Path(file_path).name
                )
                if archived:
                    archived_files.append(archived)
            
            logger.info(f"✅ 分离完成，共{len(archived_files)}个年度报告")
            return archived_files
            
        except Exception as e:
            logger.error(f"分离财务报告失败: {e}", exc_info=True)
            return []
    
    def _detect_year_ranges(self, reader: PdfReader) -> List[Dict]:
        """
        检测年份范围
        
        Returns:
            [
                {'year': 2023, 'start_page': 0, 'end_page': 14, 'pages': [0,1,2,...]},
                {'year': 2022, 'start_page': 15, 'end_page': 29, 'pages': [15,16,...]},
                ...
            ]
        """
        total_pages = len(reader.pages)
        page_years = []  # [(page_num, year), ...]
        
        # 1. 为每一页检测年份
        for page_num in range(total_pages):
            try:
                text = reader.pages[page_num].extract_text()[:2000]  # 只看前2000字符
                detected_year = self._extract_year_from_text(text)
                if detected_year:
                    page_years.append((page_num, detected_year))
                    logger.debug(f"  页{page_num+1}: 检测到{detected_year}年")
            except Exception as e:
                logger.warning(f"页{page_num+1}解析失败: {e}")
                continue
        
        if not page_years:
            return []
        
        # 2. 聚类为年份范围
        year_ranges = []
        current_year = None
        current_range = {'year': None, 'pages': [], 'start_page': None, 'end_page': None}
        
        for page_num, year in page_years:
            if current_year is None:
                # 第一个年份
                current_year = year
                current_range = {
                    'year': year,
                    'pages': [page_num],
                    'start_page': page_num,
                    'end_page': page_num
                }
            elif year == current_year:
                # 同一年份，扩展范围
                current_range['pages'].append(page_num)
                current_range['end_page'] = page_num
            else:
                # 新年份，保存当前范围
                if len(current_range['pages']) >= 3:  # 至少3页才算有效
                    # 填充中间未检测到年份的页面
                    start = current_range['start_page']
                    end = current_range['end_page']
                    current_range['pages'] = list(range(start, end + 1))
                    year_ranges.append(current_range)
                
                # 开始新范围
                current_year = year
                current_range = {
                    'year': year,
                    'pages': [page_num],
                    'start_page': page_num,
                    'end_page': page_num
                }
        
        # 添加最后一个范围
        if current_range and len(current_range['pages']) >= 3:
            start = current_range['start_page']
            end = current_range['end_page']
            current_range['pages'] = list(range(start, end + 1))
            year_ranges.append(current_range)
        
        logger.info(f"检测到{len(year_ranges)}个年度报告: {[r['year'] for r in year_ranges]}")
        return year_ranges
    
    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """从文本中提取年份"""
        for pattern in self.YEAR_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    year = int(match)
                    if 2000 <= year <= 2030:  # 合理范围
                        return year
                except:
                    continue
        return None
    
    def _save_year_report(
        self,
        reader: PdfReader,
        year: int,
        pages: List[int],
        file_id: str,
        original_filename: str
    ) -> Optional[Dict]:
        """
        保存单个年度报告
        
        Returns:
            {
                'year': 2023,
                'archive_path': '...',
                'page_count': 15,
                'file_size': 1234567,
                'archived_at': '2025-12-14 10:30:00'
            }
        """
        try:
            # 创建年份目录
            year_dir = self.financial_dir / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名: YYYY-MM-DD_原始文件名_YYYY年报.pdf
            date_str = datetime.now().strftime('%Y-%m-%d')
            base_name = Path(original_filename).stem
            archive_filename = f"{date_str}_{base_name}_{year}年财务报告.pdf"
            archive_path = year_dir / archive_filename
            
            # 提取页面并保存
            writer = PdfWriter()
            for page_num in pages:
                writer.add_page(reader.pages[page_num])
            
            with open(archive_path, 'wb') as f:
                writer.write(f)
            
            file_size = archive_path.stat().st_size
            
            logger.info(f"  ✅ {year}年报告已保存: {archive_path.name} ({len(pages)}页, {file_size//1024}KB)")
            
            # 保存到数据库
            self._save_to_database(
                file_id=file_id,
                year=year,
                archive_path=str(archive_path),
                page_count=len(pages),
                file_size=file_size
            )
            
            return {
                'year': year,
                'archive_path': str(archive_path),
                'page_count': len(pages),
                'file_size': file_size,
                'archived_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"保存{year}年报告失败: {e}", exc_info=True)
            return None
    
    def _save_as_single_file(self, file_path: str, file_id: str, total_pages: int) -> List[Dict]:
        """未检测到年份时，保存为单个文件"""
        try:
            # 使用unknown目录
            unknown_dir = self.financial_dir / "unknown"
            unknown_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = Path(file_path).name
            archive_path = unknown_dir / f"{date_str}_{filename}"
            
            shutil.copy2(file_path, archive_path)
            file_size = archive_path.stat().st_size
            
            logger.info(f"  ⚠️ 未知年份报告已保存: {archive_path.name}")
            
            self._save_to_database(
                file_id=file_id,
                year=None,
                archive_path=str(archive_path),
                page_count=total_pages,
                file_size=file_size
            )
            
            return [{
                'year': None,
                'archive_path': str(archive_path),
                'page_count': total_pages,
                'file_size': file_size,
                'archived_at': datetime.now().isoformat()
            }]
            
        except Exception as e:
            logger.error(f"保存单个文件失败: {e}", exc_info=True)
            return []
    
    def _save_to_database(
        self,
        file_id: str,
        year: Optional[int],
        archive_path: str,
        page_count: int,
        file_size: int
    ):
        """保存到数据库"""
        try:
            db.execute("""
                INSERT INTO financial_reports 
                (id, file_id, year, archive_path, page_count, file_size, archived_at)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (file_id, year) 
                DO UPDATE SET 
                    archive_path = EXCLUDED.archive_path,
                    page_count = EXCLUDED.page_count,
                    file_size = EXCLUDED.file_size,
                    archived_at = NOW()
            """, (file_id, year, archive_path, page_count, file_size))
            
            logger.debug(f"  数据库记录已保存: file_id={file_id}, year={year}")
            
        except Exception as e:
            logger.error(f"保存数据库记录失败: {e}", exc_info=True)
    
    def get_archived_reports(self, file_id: str) -> List[Dict]:
        """获取已存档的报告列表"""
        try:
            result = db.query_all("""
                SELECT year, archive_path, page_count, file_size, archived_at
                FROM financial_reports
                WHERE file_id = %s
                ORDER BY year DESC NULLS LAST
            """, (file_id,))
            
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            logger.error(f"查询存档报告失败: {e}", exc_info=True)
            return []
