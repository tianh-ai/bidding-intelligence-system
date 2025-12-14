"""
OCR和混合文本提取引擎
用于处理扫描PDF、混合PDF等需要OCR的文件
"""

import io
import asyncio
from typing import Optional, List, Dict
from abc import ABC, abstractmethod

from core.logger import logger


class TextExtractorBase(ABC):
    """文本提取器基类"""
    
    @abstractmethod
    async def extract(self, page_data) -> str:
        """提取页面文本"""
        pass


class DirectTextExtractor(TextExtractorBase):
    """直接文本流提取（无OCR）"""
    
    async def extract(self, page) -> str:
        """从PDF页面提取嵌入文本"""
        try:
            text = page.extract_text() or ""
            return text.strip()
        except Exception as e:
            logger.warning(f"文本提取失败: {e}")
            return ""


class PaddleOCRExtractor(TextExtractorBase):
    """使用PaddleOCR的提取器"""
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._ocr = None
    
    @property
    def ocr(self):
        """延迟初始化OCR引擎"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                logger.info("初始化PaddleOCR...")
                self._ocr = PaddleOCR(
                    use_gpu=self.use_gpu,
                    lang='ch',  # 中文
                    ocr_version='PP-OCRv3',  # 最新版本
                    show_log=False
                )
                logger.info("PaddleOCR初始化成功")
            except ImportError:
                logger.error("PaddleOCR未安装，请执行: pip install paddlepaddle paddleocr")
                raise
        
        return self._ocr
    
    async def extract(self, page_image: bytes) -> str:
        """
        使用OCR识别图像
        
        Args:
            page_image: 页面图像字节
            
        Returns:
            识别的文本
        """
        try:
            from PIL import Image
            import numpy as np
            
            # 加载图像
            image = Image.open(io.BytesIO(page_image))
            image_array = np.array(image)
            
            # OCR识别
            results = self.ocr.ocr(image_array, cls=True)
            
            # 合并文本（保持行序）
            text_lines = []
            if results:
                for line in results:
                    if line:
                        # 每行的识别结果
                        line_text = ' '.join([item[1] for item in line])
                        text_lines.append(line_text)
            
            return '\n'.join(text_lines)
        
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return ""


class HybridTextExtractor:
    """混合文本提取器（文本流 + OCR）"""
    
    def __init__(self, use_paddle_ocr: bool = True):
        self.direct_extractor = DirectTextExtractor()
        self.ocr_extractor = PaddleOCRExtractor() if use_paddle_ocr else None
    
    async def extract_from_pdf_page(self, page) -> Dict[str, str]:
        """
        从PDF页面提取文本，自动选择最佳方式
        
        Returns:
            {
                'text': '提取的文本',
                'method': 'direct' | 'ocr',
                'confidence': 0-1
            }
        """
        # Step 1: 尝试直接文本提取
        direct_text = await self.direct_extractor.extract(page)
        
        if direct_text and len(direct_text) > 100:
            # 文本足够，直接返回
            return {
                'text': direct_text,
                'method': 'direct',
                'confidence': 0.95
            }
        
        # Step 2: 文本不足，尝试OCR
        if self.ocr_extractor is None:
            logger.warning("PaddleOCR未配置，无法识别扫描页")
            return {
                'text': direct_text or "",
                'method': 'direct',
                'confidence': 0.5
            }
        
        logger.info("页面文本不足，使用OCR识别...")
        
        try:
            # 渲染页面为图像
            from pypdf import PdfReader
            import io
            from PIL import Image
            
            # 将PDF页渲染为高分辨率图像
            pix = page.render(zoom_x=2, zoom_y=2)  # 2倍分辨率
            image_bytes = pix.tobytes()
            image = Image.frombytes("RGB", (pix.width, pix.height), image_bytes)
            
            # 转为字节
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes = img_bytes.getvalue()
            
            # OCR识别
            ocr_text = await self.ocr_extractor.extract(img_bytes)
            
            # 合并结果（优先OCR）
            merged_text = ocr_text if ocr_text else direct_text
            
            return {
                'text': merged_text,
                'method': 'ocr',
                'confidence': 0.85
            }
        
        except Exception as e:
            logger.error(f"OCR处理失败: {e}")
            return {
                'text': direct_text or "",
                'method': 'direct',
                'confidence': 0.5
            }
    
    async def extract_document(self, pdf_path: str) -> List[Dict]:
        """
        提取整个PDF文档的文本
        
        Returns:
            [
                {'page_num': 0, 'text': '...', 'method': 'direct', 'confidence': 0.95},
                {'page_num': 1, 'text': '...', 'method': 'ocr', 'confidence': 0.85},
                ...
            ]
        """
        from pypdf import PdfReader
        
        reader = PdfReader(pdf_path)
        results = []
        
        for page_num, page in enumerate(reader.pages):
            logger.info(f"处理页面 {page_num + 1}/{len(reader.pages)}")
            
            result = await self.extract_from_pdf_page(page)
            result['page_num'] = page_num
            results.append(result)
        
        return results


class ImageMetadataExtractor:
    """图片元数据提取器"""
    
    @staticmethod
    def extract_metadata(file_path: str) -> Dict:
        """
        提取图片元数据
        
        Returns:
            {
                'filename': '图片名',
                'size': (width, height),
                'format': 'PNG',
                'file_size': 1024,
                'position': 0  # 在文档中的位置
            }
        """
        try:
            from PIL import Image
            import os
            
            img = Image.open(file_path)
            file_size = os.path.getsize(file_path)
            
            return {
                'filename': os.path.basename(file_path),
                'size': img.size,
                'format': img.format,
                'file_size': file_size,
                'dpi': img.info.get('dpi'),
                'timestamp': os.path.getmtime(file_path)
            }
        
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            return {}


class DocumentImageExtractor:
    """从PDF中提取并保存图片"""
    
    @staticmethod
    async def extract_images_from_pdf(pdf_path: str, output_dir: str) -> List[Dict]:
        """
        从PDF提取所有图片
        
        Returns:
            [
                {
                    'page': 0,
                    'image_num': 0,
                    'filename': 'page_0_image_0.png',
                    'size': (800, 600),
                    'is_likely_scan': False  # 是否看起来是扫描页的一部分
                },
                ...
            ]
        """
        from pypdf import PdfReader
        from PIL import Image
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        reader = PdfReader(pdf_path)
        extracted = []
        
        for page_num, page in enumerate(reader.pages):
            image_list = page.images
            
            for img_num, image in enumerate(image_list):
                try:
                    # 保存图片
                    filename = f"page_{page_num:04d}_img_{img_num:03d}.png"
                    filepath = os.path.join(output_dir, filename)
                    
                    # 图片已提取，直接保存
                    with open(filepath, 'wb') as f:
                        f.write(image.get_data())
                    
                    # 估算尺寸
                    img = Image.open(filepath)
                    size = img.size
                    
                    # 判断是否为扫描页（高分辨率，通常>300dpi）
                    is_scan = size[0] > 2000 or size[1] > 2000
                    
                    extracted.append({
                        'page': page_num,
                        'image_num': img_num,
                        'filename': filename,
                        'size': size,
                        'is_likely_scan': is_scan,
                        'filepath': filepath
                    })
                
                except Exception as e:
                    logger.warning(f"页 {page_num} 图片 {img_num} 提取失败: {e}")
        
        return extracted
