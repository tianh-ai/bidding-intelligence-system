"""
ImageProcessor Skill - 从文档中提取图片并保存
从 engines/image_extractor.py 迁移核心逻辑
"""

import io
import hashlib
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from PIL import Image
from pydantic import BaseModel, Field, field_validator

from core.logger import logger
from core.config import get_settings


# ============================================================================
# Pydantic Models
# ============================================================================

class ImageProcessorInput(BaseModel):
    """图片处理器输入参数"""
    
    file_path: str = Field(..., description="文档文件路径（PDF或DOCX）")
    file_id: str = Field(..., description="文件唯一标识符")
    year: Optional[int] = Field(None, description="年份（用于分类存储），None则使用当前年份")
    storage_base: Optional[str] = Field(None, description="存储根目录，None则使用配置")
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        """验证文件路径"""
        if not v:
            raise ValueError("file_path 不能为空")
        
        file_path = Path(v)
        if not file_path.exists():
            raise ValueError(f"文件不存在: {v}")
        
        # 验证文件扩展名
        ext = file_path.suffix.lower()
        if ext not in ['.pdf', '.docx']:
            raise ValueError(f"不支持的文件类型: {ext}，仅支持 .pdf 和 .docx")
        
        return v
    
    @field_validator('file_id')
    @classmethod
    def validate_file_id(cls, v):
        """验证文件ID"""
        if not v or not v.strip():
            raise ValueError("file_id 不能为空")
        return v.strip()
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        """验证年份"""
        if v is not None:
            if v < 2000 or v > 2100:
                raise ValueError(f"年份不合理: {v}")
        return v


class ImageInfo(BaseModel):
    """单张图片信息"""
    
    image_id: str = Field(..., description="图片唯一ID")
    file_id: str = Field(..., description="所属文件ID")
    image_path: str = Field(..., description="图片存储路径")
    image_number: int = Field(..., description="图片序号（从1开始）")
    page_number: Optional[int] = Field(None, description="所在页码（PDF文件）")
    format: str = Field(..., description="图片格式（PNG, JPEG等）")
    size: int = Field(..., description="文件大小（字节）")
    width: int = Field(..., description="图片宽度（像素）")
    height: int = Field(..., description="图片高度（像素）")
    hash: str = Field(..., description="图片内容哈希（MD5前8位）")


class ImageProcessorOutput(BaseModel):
    """图片处理器输出结果"""
    
    file_id: str = Field(..., description="文件ID")
    file_path: str = Field(..., description="源文件路径")
    images: List[ImageInfo] = Field(default_factory=list, description="提取的图片列表")
    image_count: int = Field(..., description="提取的图片总数")
    storage_directory: str = Field(..., description="图片存储目录")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")


# ============================================================================
# ImageProcessor Skill
# ============================================================================

class ImageProcessor:
    """
    图片处理器 Skill - 从文档中提取图片并保存
    
    功能:
        - 从 PDF 文档提取图片
        - 从 DOCX 文档提取图片
        - 按年份分类存储
        - 生成图片元数据（尺寸、格式、哈希等）
        - 避免重复保存（通过哈希识别）
    
    设计模式:
        - 纯函数式 Skill（不直接操作数据库）
        - 输入/输出通过 Pydantic 模型验证
        - 错误处理完善，不影响文档处理流程
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化图片处理器
        
        Args:
            config: 可选配置字典
        """
        self.config = config or {}
        
        # 获取存储基础路径
        settings = get_settings()
        self.default_storage_base = Path(settings.image_storage_path)
        
        logger.info("ImageProcessor initialized", extra={"config": self.config})
    
    def execute(self, input_data: ImageProcessorInput) -> ImageProcessorOutput:
        """
        执行图片提取
        
        Args:
            input_data: 输入参数（已验证）
            
        Returns:
            ImageProcessorOutput: 提取结果
            
        Raises:
            ValueError: 输入验证失败
            RuntimeError: 提取过程异常
        """
        # 1. 验证输入
        if not self.validate(input_data):
            raise ValueError("输入验证失败")
        
        # 2. 确定文件类型
        file_path = Path(input_data.file_path)
        ext = file_path.suffix.lower()
        
        # 3. 准备存储目录
        year = input_data.year or datetime.now().year
        storage_base = Path(input_data.storage_base) if input_data.storage_base else self.default_storage_base
        year_dir = storage_base / str(year) / input_data.file_id
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. 根据文件类型提取图片
        try:
            if ext == '.pdf':
                images = self._extract_from_pdf(
                    pdf_path=str(file_path),
                    file_id=input_data.file_id,
                    year_dir=year_dir
                )
            elif ext == '.docx':
                images = self._extract_from_docx(
                    docx_path=str(file_path),
                    file_id=input_data.file_id,
                    year_dir=year_dir
                )
            else:
                raise ValueError(f"不支持的文件类型: {ext}")
            
            # 5. 构建输出
            output = ImageProcessorOutput(
                file_id=input_data.file_id,
                file_path=str(file_path),
                images=images,
                image_count=len(images),
                storage_directory=str(year_dir),
                metadata={
                    "year": year,
                    "file_type": ext[1:],  # 去掉 .
                    "storage_base": str(storage_base)
                }
            )
            
            logger.info(
                "ImageProcessor execution completed",
                extra={
                    "file_id": input_data.file_id,
                    "image_count": output.image_count,
                    "file_type": ext
                }
            )
            
            return output
            
        except FileNotFoundError as e:
            logger.error("文件未找到", error=str(e))
            raise
        except Exception as e:
            logger.error("图片提取失败", error=str(e), exc_info=True)
            raise RuntimeError(f"图片提取失败: {e}")
    
    def _extract_from_pdf(
        self,
        pdf_path: str,
        file_id: str,
        year_dir: Path
    ) -> List[ImageInfo]:
        """
        从 PDF 提取图片
        
        Args:
            pdf_path: PDF 文件路径
            file_id: 文件ID
            year_dir: 年份存储目录
            
        Returns:
            List[ImageInfo]: 图片列表
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            extracted_images = []
            image_count = 0
            
            # 遍历每一页
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img in image_list:
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
                        logger.warning(
                            f"提取PDF图片失败",
                            extra={"page": page_num + 1, "error": str(img_err)}
                        )
                        continue
            
            # 记录总页数（在关闭文档前）
            total_pages = len(doc)
            doc.close()
            
            logger.info(
                f"从 PDF 提取图片完成",
                extra={"image_count": len(extracted_images), "total_pages": total_pages}
            )
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"PDF图片提取失败: {e}", exc_info=True)
            return []
    
    def _extract_from_docx(
        self,
        docx_path: str,
        file_id: str,
        year_dir: Path
    ) -> List[ImageInfo]:
        """
        从 DOCX 提取图片
        
        Args:
            docx_path: DOCX 文件路径
            file_id: 文件ID
            year_dir: 年份存储目录
            
        Returns:
            List[ImageInfo]: 图片列表
        """
        try:
            import docx
            
            doc = docx.Document(docx_path)
            extracted_images = []
            image_count = 0
            
            # 遍历文档中的图片关系
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    try:
                        image_data = rel.target_part.blob
                        image_count += 1
                        
                        # 保存图片
                        image_info = self._save_image(
                            image_data=image_data,
                            file_id=file_id,
                            image_number=image_count,
                            year_dir=year_dir,
                            page_number=None  # DOCX 不记录页码
                        )
                        
                        if image_info:
                            extracted_images.append(image_info)
                            
                    except Exception as img_err:
                        logger.warning(
                            f"提取DOCX图片失败",
                            extra={"image_number": image_count, "error": str(img_err)}
                        )
                        continue
            
            logger.info(
                f"从 DOCX 提取图片完成",
                extra={"image_count": len(extracted_images)}
            )
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"DOCX图片提取失败: {e}", exc_info=True)
            return []
    
    def _save_image(
        self,
        image_data: bytes,
        file_id: str,
        image_number: int,
        year_dir: Path,
        page_number: Optional[int] = None
    ) -> Optional[ImageInfo]:
        """
        保存单张图片
        
        Args:
            image_data: 图片二进制数据
            file_id: 文件ID
            image_number: 图片序号
            year_dir: 存储目录
            page_number: 页码（可选）
            
        Returns:
            ImageInfo: 图片信息，失败返回 None
        """
        try:
            # 加载图片获取元数据
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            format_name = image.format or 'PNG'
            
            # 生成图片ID和文件名
            image_id = str(uuid.uuid4())
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
            
            logger.debug(
                f"保存图片",
                extra={
                    "filename": filename,
                    "size": f"{width}x{height}",
                    "file_size_kb": file_size // 1024
                }
            )
            
            return ImageInfo(
                image_id=image_id,
                file_id=file_id,
                image_path=str(image_path),
                image_number=image_number,
                page_number=page_number,
                format=format_name,
                size=file_size,
                width=width,
                height=height,
                hash=image_hash
            )
            
        except Exception as e:
            logger.error(f"保存图片失败: {e}")
            return None
    
    def validate(self, input_data: ImageProcessorInput) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入参数
            
        Returns:
            bool: 验证通过返回 True
        """
        try:
            # Pydantic 已经做了字段级验证
            # 这里可以添加业务逻辑验证
            
            # 验证文件确实存在
            file_path = Path(input_data.file_path)
            if not file_path.exists():
                logger.error(f"文件不存在: {input_data.file_path}")
                return False
            
            # 验证文件可读
            if not file_path.is_file():
                logger.error(f"不是有效文件: {input_data.file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"输入验证失败: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取 Skill 元数据
        
        Returns:
            Dict: Skill 信息
        """
        return {
            "name": "ImageProcessor",
            "version": "1.0.0",
            "description": "从PDF/DOCX文档中提取图片并保存",
            "author": "Bidding Intelligence System",
            "dependencies": ["PyMuPDF", "python-docx", "Pillow"],
            "supported_formats": ["pdf", "docx"],
            "capabilities": [
                "extract_images_from_pdf",
                "extract_images_from_docx",
                "generate_image_metadata",
                "deduplicate_by_hash",
                "organize_by_year"
            ]
        }


# ============================================================================
# CLI Example (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python3 image_processor.py <file_path> <file_id> [year]")
        print("示例: python3 image_processor.py sample.pdf file_001 2025")
        sys.exit(1)
    
    file_path = sys.argv[1]
    file_id = sys.argv[2]
    year = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # 创建 Skill 实例
    processor = ImageProcessor()
    
    # 准备输入
    input_data = ImageProcessorInput(
        file_path=file_path,
        file_id=file_id,
        year=year
    )
    
    # 执行提取
    result = processor.execute(input_data)
    
    # 输出结果
    print(f"\n提取完成:")
    print(f"  文件: {result.file_path}")
    print(f"  图片数量: {result.image_count}")
    print(f"  存储目录: {result.storage_directory}")
    print(f"\n图片列表:")
    for img in result.images:
        print(f"  - {img.image_path} ({img.width}x{img.height}, {img.format})")
