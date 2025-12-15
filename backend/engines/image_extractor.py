"""
图片提取和存储引擎
从DOCX/PDF文档中提取图片并按年份存档
"""

import os
import io
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from PIL import Image

from core.logger import logger
from core.config import get_settings
from database import db


class ImageExtractor:
    """图片提取器 - 保存原始图片，不进行OCR"""
    
    def __init__(self, storage_base: Optional[str] = None):
        settings = get_settings()
        base_path = storage_base or settings.image_storage_path
        self.storage_base = Path(base_path)
        self.storage_base.mkdir(parents=True, exist_ok=True)
        logger.info(f"图片存储目录: {self.storage_base}")
    
    def extract_from_docx(
        self, 
        docx_path: str, 
        file_id: str,
        year: Optional[int] = None
    ) -> List[Dict]:
        """
        从DOCX文件提取图片并保存
        
        Args:
            docx_path: DOCX文件路径
            file_id: 文件ID
            year: 年份（用于分类），None则使用当前年份
            
        Returns:
            List[Dict]: 提取的图片信息
            [
                {
                    'image_id': 'uuid',
                    'file_id': 'xxx',
                    'image_path': '/path/to/image.png',
                    'image_number': 1,
                    'format': 'PNG',
                    'size': 123456,
                    'width': 800,
                    'height': 600
                },
                ...
            ]
        """
        try:
            import docx
            doc = docx.Document(docx_path)
            
            # 确定年份目录
            if year is None:
                year = datetime.now().year
            
            year_dir = self.storage_base / str(year) / file_id
            year_dir.mkdir(parents=True, exist_ok=True)
            
            extracted_images = []
            image_count = 0
            
            # 遍历文档中的图片关系
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    try:
                        image_data = rel.target_part.blob
                        image_count += 1
                        
                        # 生成图片信息
                        image_info = self._save_image(
                            image_data=image_data,
                            file_id=file_id,
                            image_number=image_count,
                            year_dir=year_dir
                        )
                        
                        if image_info:
                            extracted_images.append(image_info)
                            
                    except Exception as img_err:
                        logger.warning(f"提取图片 {image_count} 失败: {img_err}")
                        continue
            
            logger.info(f"从 {os.path.basename(docx_path)} 提取了 {len(extracted_images)} 张图片")
            
            # 保存到数据库
            self._save_to_database(extracted_images)
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"DOCX图片提取失败: {e}", exc_info=True)
            return []
    
    def extract_from_pdf(
        self,
        pdf_path: str,
        file_id: str,
        year: Optional[int] = None
    ) -> List[Dict]:
        """
        从PDF文件提取图片并保存
        
        Args:
            pdf_path: PDF文件路径
            file_id: 文件ID
            year: 年份
            
        Returns:
            List[Dict]: 提取的图片信息
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            
            # 确定年份目录
            if year is None:
                year = datetime.now().year
            
            year_dir = self.storage_base / str(year) / file_id
            year_dir.mkdir(parents=True, exist_ok=True)
            
            extracted_images = []
            image_count = 0
            
            # 遍历每一页
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_data = base_image["image"]
                        
                        image_count += 1
                        
                        # 保存图片
                        image_info = self._save_image(
                            image_data=image_data,
                            file_id=file_id,
                            image_number=image_count,
                            year_dir=year_dir,
                            page_number=page_num + 1
                        )
                        
                        if image_info:
                            extracted_images.append(image_info)
                            
                    except Exception as img_err:
                        logger.warning(f"提取PDF图片失败 (页{page_num+1}): {img_err}")
                        continue
            
            logger.info(f"从 {os.path.basename(pdf_path)} 提取了 {len(extracted_images)} 张图片")
            
            # 保存到数据库
            self._save_to_database(extracted_images)
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"PDF图片提取失败: {e}", exc_info=True)
            return []
    
    def _save_image(
        self,
        image_data: bytes,
        file_id: str,
        image_number: int,
        year_dir: Path,
        page_number: Optional[int] = None
    ) -> Optional[Dict]:
        """
        保存单张图片
        
        Returns:
            Dict: 图片信息，失败返回None
        """
        try:
            # 加载图片获取元数据
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            format_name = image.format or 'PNG'
            
            # 生成图片ID和文件名
            import uuid
            image_id = str(uuid.uuid4())
            
            # 文件名: {序号}_{hash前8位}.{格式}
            image_hash = hashlib.md5(image_data).hexdigest()[:8]
            if page_number:
                filename = f"{image_number:03d}_page{page_number}_{image_hash}.{format_name.lower()}"
            else:
                filename = f"{image_number:03d}_{image_hash}.{format_name.lower()}"
            
            image_path = year_dir / filename
            
            # 保存图片
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            file_size = len(image_data)
            
            logger.debug(f"保存图片: {filename} ({width}x{height}, {file_size//1024}KB)")
            
            return {
                'image_id': image_id,
                'file_id': file_id,
                'image_path': str(image_path),
                'image_number': image_number,
                'page_number': page_number,
                'format': format_name,
                'size': file_size,
                'width': width,
                'height': height,
                'hash': image_hash
            }
            
        except Exception as e:
            logger.error(f"保存图片失败: {e}")
            return None
    
    def _save_to_database(self, images: List[Dict]):
        """保存图片记录到数据库"""
        if not images:
            return
        
        try:
            for img in images:
                db.execute("""
                    INSERT INTO extracted_images 
                    (id, file_id, image_path, image_number, page_number, 
                     format, size, width, height, hash, extracted_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id) DO NOTHING
                """, (
                    img['image_id'],
                    img['file_id'],
                    img['image_path'],
                    img['image_number'],
                    img.get('page_number'),
                    img['format'],
                    img['size'],
                    img['width'],
                    img['height'],
                    img['hash']
                ))
            
            logger.info(f"数据库保存了 {len(images)} 条图片记录")
            
        except Exception as e:
            logger.error(f"保存图片记录到数据库失败: {e}", exc_info=True)
    
    def get_file_images(self, file_id: str) -> List[Dict]:
        """获取文件的所有图片"""
        try:
            result = db.query_all("""
                SELECT 
                    id as image_id,
                    image_path,
                    image_number,
                    page_number,
                    format,
                    size,
                    width,
                    height,
                    extracted_at
                FROM extracted_images
                WHERE file_id = %s
                ORDER BY image_number
            """, (file_id,))
            
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            logger.error(f"查询文件图片失败: {e}")
            return []
    
    def get_images_by_year(self, year: int) -> List[Dict]:
        """获取指定年份的所有图片"""
        try:
            result = db.query_all("""
                SELECT 
                    ei.id as image_id,
                    ei.file_id,
                    ei.image_path,
                    ei.image_number,
                    ei.format,
                    ei.size,
                    uf.filename as source_filename
                FROM extracted_images ei
                LEFT JOIN uploaded_files uf ON ei.file_id = uf.id
                WHERE ei.image_path LIKE %s
                ORDER BY ei.extracted_at DESC
            """, (f'%/{year}/%',))
            
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            logger.error(f"查询年度图片失败: {e}")
            return []
    
    def cleanup_orphaned_images(self):
        """清理孤立的图片（对应文件已删除）"""
        try:
            # 查找数据库中有记录但文件已删除的图片
            orphaned = db.query_all("""
                SELECT ei.image_path
                FROM extracted_images ei
                LEFT JOIN uploaded_files uf ON ei.file_id = uf.id
                WHERE uf.id IS NULL
            """)
            
            deleted_count = 0
            for row in orphaned:
                image_path = Path(row['image_path'])
                if image_path.exists():
                    image_path.unlink()
                    deleted_count += 1
            
            # 删除数据库记录
            db.execute("""
                DELETE FROM extracted_images
                WHERE file_id NOT IN (SELECT id FROM uploaded_files)
            """)
            
            logger.info(f"清理了 {deleted_count} 个孤立图片文件")
            
        except Exception as e:
            logger.error(f"清理孤立图片失败: {e}")
