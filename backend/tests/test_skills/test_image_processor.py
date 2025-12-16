"""
ImageProcessor Skill 单元测试
测试图片提取、保存、元数据生成等功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from skills.image_processor import (
    ImageProcessor,
    ImageProcessorInput,
    ImageProcessorOutput,
    ImageInfo
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def processor():
    """创建 ImageProcessor 实例"""
    return ImageProcessor()


@pytest.fixture
def temp_storage():
    """创建临时存储目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_image_data():
    """生成示例图片数据"""
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def mock_pdf_file(tmp_path):
    """创建模拟 PDF 文件"""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_text("mock pdf content")
    return str(pdf_file)


@pytest.fixture
def mock_docx_file(tmp_path):
    """创建模拟 DOCX 文件"""
    docx_file = tmp_path / "sample.docx"
    docx_file.write_text("mock docx content")
    return str(docx_file)


# ============================================================================
# 测试类
# ============================================================================

class TestImageProcessorBasic:
    """基础功能测试"""
    
    def test_initialization(self, processor):
        """测试初始化"""
        assert processor is not None
        assert hasattr(processor, 'default_storage_base')
        assert hasattr(processor, 'config')
    
    def test_initialization_with_config(self):
        """测试带配置初始化"""
        config = {"max_size": 10000000}
        processor = ImageProcessor(config=config)
        assert processor.config == config
    
    def test_get_metadata(self, processor):
        """测试获取元数据"""
        metadata = processor.get_metadata()
        
        assert metadata['name'] == 'ImageProcessor'
        assert metadata['version'] == '1.0.0'
        assert 'description' in metadata
        assert 'dependencies' in metadata
        assert 'PyMuPDF' in metadata['dependencies']
        assert 'python-docx' in metadata['dependencies']
        assert 'pdf' in metadata['supported_formats']
        assert 'docx' in metadata['supported_formats']


class TestImageProcessorValidation:
    """输入验证测试"""
    
    def test_validate_valid_input(self, processor, mock_pdf_file):
        """测试有效输入验证"""
        input_data = ImageProcessorInput(
            file_path=mock_pdf_file,
            file_id="test_001"
        )
        
        assert processor.validate(input_data) is True
    
    def test_validate_empty_path(self, processor):
        """测试空路径验证"""
        with pytest.raises(ValueError, match="file_path 不能为空"):
            ImageProcessorInput(
                file_path="",
                file_id="test_001"
            )
    
    def test_validate_nonexistent_file(self, processor):
        """测试不存在的文件"""
        with pytest.raises(ValueError, match="文件不存在"):
            ImageProcessorInput(
                file_path="/nonexistent/file.pdf",
                file_id="test_001"
            )
    
    def test_validate_unsupported_format(self, processor, tmp_path):
        """测试不支持的文件格式"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test")
        
        with pytest.raises(ValueError, match="不支持的文件类型"):
            ImageProcessorInput(
                file_path=str(txt_file),
                file_id="test_001"
            )
    
    def test_validate_empty_file_id(self, processor, mock_pdf_file):
        """测试空文件ID"""
        with pytest.raises(ValueError, match="file_id 不能为空"):
            ImageProcessorInput(
                file_path=mock_pdf_file,
                file_id=""
            )
    
    def test_validate_invalid_year(self, processor, mock_pdf_file):
        """测试无效年份"""
        with pytest.raises(ValueError, match="年份不合理"):
            ImageProcessorInput(
                file_path=mock_pdf_file,
                file_id="test_001",
                year=1900
            )


class TestImageSaving:
    """图片保存测试"""
    
    def test_save_image_success(self, processor, sample_image_data, temp_storage):
        """测试成功保存图片"""
        year_dir = Path(temp_storage) / "2025" / "test_file"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        image_info = processor._save_image(
            image_data=sample_image_data,
            file_id="test_file",
            image_number=1,
            year_dir=year_dir,
            page_number=None
        )
        
        assert image_info is not None
        assert isinstance(image_info, ImageInfo)
        assert image_info.file_id == "test_file"
        assert image_info.image_number == 1
        assert image_info.width == 100
        assert image_info.height == 100
        assert image_info.format == 'PNG'
        assert image_info.size == len(sample_image_data)
        assert len(image_info.hash) == 8
        assert Path(image_info.image_path).exists()
    
    def test_save_image_with_page_number(self, processor, sample_image_data, temp_storage):
        """测试保存图片（带页码）"""
        year_dir = Path(temp_storage) / "2025" / "test_file"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        image_info = processor._save_image(
            image_data=sample_image_data,
            file_id="test_file",
            image_number=3,
            year_dir=year_dir,
            page_number=5
        )
        
        assert image_info is not None
        assert image_info.page_number == 5
        assert "page5" in image_info.image_path
        assert "003_" in image_info.image_path  # 序号格式化为 003
    
    def test_save_image_invalid_data(self, processor, temp_storage):
        """测试保存无效图片数据"""
        year_dir = Path(temp_storage) / "2025" / "test_file"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        image_info = processor._save_image(
            image_data=b"invalid image data",
            file_id="test_file",
            image_number=1,
            year_dir=year_dir
        )
        
        # 应该返回 None（失败）
        assert image_info is None


class TestPDFExtraction:
    """PDF 图片提取测试"""
    
    def test_extract_from_pdf_mock(self, processor, sample_image_data, temp_storage):
        """测试从 PDF 提取图片（模拟）"""
        year_dir = Path(temp_storage) / "2025" / "test_file"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # 模拟 PyMuPDF（在函数内部import，需要patch sys.modules）
        import sys
        mock_fitz = MagicMock()
        with patch.dict(sys.modules, {'fitz': mock_fitz}):
            # 模拟文档
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1  # 1页
            
            # 模拟页面
            mock_page = MagicMock()
            mock_page.get_images.return_value = [[123, 0, 0, 0, 0, 0, 0]]  # xref=123
            
            mock_doc.__getitem__.return_value = mock_page
            mock_doc.extract_image.return_value = {"image": sample_image_data}
            
            mock_fitz.open.return_value = mock_doc
            
            # 执行提取
            images = processor._extract_from_pdf(
                pdf_path="/fake/path.pdf",
                file_id="test_file",
                year_dir=year_dir
            )
            
            assert len(images) == 1
            assert images[0].image_number == 1
            assert images[0].page_number == 1
    
    def test_extract_from_pdf_error_handling(self, processor, temp_storage):
        """测试 PDF 提取错误处理"""
        year_dir = Path(temp_storage) / "2025" / "test_file"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # 模拟 fitz.open 抛出异常
        import sys
        mock_fitz = MagicMock()
        mock_fitz.open.side_effect = Exception("File open failed")
        
        with patch.dict(sys.modules, {'fitz': mock_fitz}):
            images = processor._extract_from_pdf(
                pdf_path="/fake/path.pdf",
                file_id="test_file",
                year_dir=year_dir
            )
            
            # 应该返回空列表
            assert images == []


class TestDOCXExtraction:
    """DOCX 图片提取测试"""
    
    def test_extract_from_docx_mock(self, processor, sample_image_data, temp_storage):
        """测试从 DOCX 提取图片（模拟）"""
        year_dir = Path(temp_storage) / "2025" / "test_file"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # 模拟 python-docx
        import sys
        mock_docx = MagicMock()
        with patch.dict(sys.modules, {'docx': mock_docx}):
            # 模拟文档
            mock_doc = MagicMock()
            
            # 模拟关系（包含图片）
            mock_rel = MagicMock()
            mock_rel.target_ref = "word/media/image1.png"
            mock_rel.target_part.blob = sample_image_data
            
            mock_doc.part.rels.values.return_value = [mock_rel]
            
            mock_docx.Document.return_value = mock_doc
            
            # 执行提取
            images = processor._extract_from_docx(
                docx_path="/fake/path.docx",
                file_id="test_file",
                year_dir=year_dir
            )
            
            assert len(images) == 1
            assert images[0].image_number == 1
            assert images[0].page_number is None  # DOCX 不记录页码
    
    def test_extract_from_docx_no_images(self, processor, temp_storage):
        """测试 DOCX 无图片情况"""
        year_dir = Path(temp_storage) / "2025" / "test_file"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        import sys
        mock_docx = MagicMock()
        with patch.dict(sys.modules, {'docx': mock_docx}):
            mock_doc = MagicMock()
            mock_doc.part.rels.values.return_value = []  # 无关系
            mock_docx.Document.return_value = mock_doc
            
            images = processor._extract_from_docx(
                docx_path="/fake/path.docx",
                file_id="test_file",
                year_dir=year_dir
            )
            
            assert images == []


class TestImageProcessorExecution:
    """完整执行流程测试"""
    
    def test_execute_pdf_success(self, processor, mock_pdf_file, sample_image_data, temp_storage):
        """测试执行 PDF 图片提取"""
        input_data = ImageProcessorInput(
            file_path=mock_pdf_file,
            file_id="test_001",
            year=2025,
            storage_base=temp_storage
        )
        
        # 模拟 PDF 提取
        with patch.object(processor, '_extract_from_pdf') as mock_extract:
            mock_image = ImageInfo(
                image_id="img_001",
                file_id="test_001",
                image_path=f"{temp_storage}/2025/test_001/001_abcd1234.png",
                image_number=1,
                page_number=1,
                format="PNG",
                size=1024,
                width=100,
                height=100,
                hash="abcd1234"
            )
            mock_extract.return_value = [mock_image]
            
            result = processor.execute(input_data)
            
            assert isinstance(result, ImageProcessorOutput)
            assert result.file_id == "test_001"
            assert result.image_count == 1
            assert len(result.images) == 1
            assert result.images[0].image_id == "img_001"
            assert result.metadata['year'] == 2025
            assert result.metadata['file_type'] == 'pdf'
    
    def test_execute_docx_success(self, processor, mock_docx_file, temp_storage):
        """测试执行 DOCX 图片提取"""
        input_data = ImageProcessorInput(
            file_path=mock_docx_file,
            file_id="test_002",
            storage_base=temp_storage
        )
        
        with patch.object(processor, '_extract_from_docx') as mock_extract:
            mock_extract.return_value = []
            
            result = processor.execute(input_data)
            
            assert result.file_id == "test_002"
            assert result.image_count == 0
            assert result.metadata['file_type'] == 'docx'
    
    def test_execute_validation_failure(self, processor):
        """测试输入验证失败"""
        with pytest.raises(ValueError):
            input_data = ImageProcessorInput(
                file_path="/nonexistent.pdf",
                file_id="test_003"
            )
            processor.execute(input_data)
    
    def test_execute_extraction_error(self, processor, mock_pdf_file, temp_storage):
        """测试提取过程异常"""
        input_data = ImageProcessorInput(
            file_path=mock_pdf_file,
            file_id="test_004",
            storage_base=temp_storage
        )
        
        # 模拟提取失败
        with patch.object(processor, '_extract_from_pdf', side_effect=Exception("提取失败")):
            with pytest.raises(RuntimeError, match="图片提取失败"):
                processor.execute(input_data)


class TestImageProcessorEdgeCases:
    """边界情况测试"""
    
    def test_year_default_to_current(self, processor, mock_pdf_file, temp_storage):
        """测试年份默认为当前年份"""
        from datetime import datetime
        current_year = datetime.now().year
        
        input_data = ImageProcessorInput(
            file_path=mock_pdf_file,
            file_id="test_005",
            year=None,  # 未指定年份
            storage_base=temp_storage
        )
        
        with patch.object(processor, '_extract_from_pdf') as mock_extract:
            mock_extract.return_value = []
            result = processor.execute(input_data)
            
            assert result.metadata['year'] == current_year
    
    def test_storage_directory_creation(self, processor, mock_pdf_file, temp_storage):
        """测试存储目录自动创建"""
        input_data = ImageProcessorInput(
            file_path=mock_pdf_file,
            file_id="test_006",
            year=2025,
            storage_base=temp_storage
        )
        
        with patch.object(processor, '_extract_from_pdf') as mock_extract:
            mock_extract.return_value = []
            processor.execute(input_data)
            
            # 验证目录已创建
            expected_dir = Path(temp_storage) / "2025" / "test_006"
            assert expected_dir.exists()
            assert expected_dir.is_dir()


class TestImageProcessorIntegration:
    """集成测试"""
    
    def test_output_serialization(self, processor):
        """测试输出序列化"""
        output = ImageProcessorOutput(
            file_id="test_007",
            file_path="/path/to/file.pdf",
            images=[],
            image_count=0,
            storage_directory="/storage/2025/test_007",
            metadata={"year": 2025}
        )
        
        # 验证可以序列化
        json_data = output.model_dump()
        assert json_data['file_id'] == "test_007"
        assert json_data['image_count'] == 0
    
    def test_image_info_model_validation(self):
        """测试 ImageInfo 模型验证"""
        image = ImageInfo(
            image_id="img_001",
            file_id="file_001",
            image_path="/storage/image.png",
            image_number=1,
            format="PNG",
            size=1024,
            width=800,
            height=600,
            hash="abcd1234"
        )
        
        assert image.image_id == "img_001"
        assert image.page_number is None  # 可选字段


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
