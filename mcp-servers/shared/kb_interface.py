"""
知识库接口定义
所有 MCP 通过这个接口访问知识库，而不是直接读取原始文件
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class ChapterData(BaseModel):
    """章节数据（从知识库返回）"""
    
    id: str = Field(description="章节ID")
    file_id: str = Field(description="所属文件ID")
    chapter_number: str = Field(description="章节编号")
    chapter_title: str = Field(description="章节标题")
    chapter_level: int = Field(description="章节层级")
    position_order: int = Field(description="章节顺序")
    content: str = Field(description="章节内容")
    
    # 结构化数据（知识库预处理）
    structure_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="章节的结构化数据（表格、列表等）"
    )
    
    # 已提取的元素
    tables: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="章节中的表格列表"
    )
    lists: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="章节中的列表"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="章节的关键词"
    )


class FileMetadata(BaseModel):
    """文件元数据（从知识库返回）"""
    
    id: str = Field(description="文件ID")
    filename: str = Field(description="文件名")
    filetype: str = Field(description="文件类型（docx/pdf等）")
    file_size: int = Field(description="文件大小（字节）")
    
    # 文件结构
    total_chapters: int = Field(description="总章节数")
    total_pages: int = Field(description="总页数（如果有）")
    
    # 时间戳
    uploaded_at: datetime = Field(description="上传时间")
    processed_at: Optional[datetime] = Field(
        default=None,
        description="知识库处理时间"
    )
    
    # 文件标记
    tags: Optional[List[str]] = Field(default=None, description="文件标签")
    is_tender: Optional[bool] = Field(
        default=None,
        description="是否是招标文件"
    )


class KBClient(BaseModel):
    """
    知识库客户端接口定义
    
    学习/检查/生成 MCP 通过这个接口查询知识库
    """
    
    # 以下是接口签名，具体实现在 backend/core/kb_client.py
    
    @staticmethod
    async def get_file_metadata(file_id: str) -> FileMetadata:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件元数据
        """
        raise NotImplementedError()
    
    @staticmethod
    async def get_chapters(file_id: str) -> List[ChapterData]:
        """
        获取文件的所有章节
        
        Args:
            file_id: 文件ID
            
        Returns:
            章节列表
        """
        raise NotImplementedError()
    
    @staticmethod
    async def get_chapter(chapter_id: str) -> ChapterData:
        """
        获取单个章节的详细数据
        
        Args:
            chapter_id: 章节ID
            
        Returns:
            章节数据
        """
        raise NotImplementedError()
    
    @staticmethod
    async def compare_chapters(
        chapter_id_1: str,
        chapter_id_2: str
    ) -> Dict[str, Any]:
        """
        比较两个章节的差异
        
        Args:
            chapter_id_1: 第一个章节ID（如招标）
            chapter_id_2: 第二个章节ID（如投标）
            
        Returns:
            差异分析结果 {
                'similarities': [...],
                'differences': [...],
                'added': [...],
                'removed': [...]
            }
        """
        raise NotImplementedError()
    
    @staticmethod
    async def compare_files(
        file_id_1: str,
        file_id_2: str
    ) -> Dict[str, Any]:
        """
        比较两个文件的全局差异
        
        Args:
            file_id_1: 文件ID 1
            file_id_2: 文件ID 2
            
        Returns:
            差异分析结果
        """
        raise NotImplementedError()
    
    @staticmethod
    async def get_chapter_structure(chapter_id: str) -> Dict[str, Any]:
        """
        获取章节的结构（标题层级、小节等）
        
        Args:
            chapter_id: 章节ID
            
        Returns:
            结构信息 {
                'sections': [...],
                'hierarchy': {...},
                'depth': int
            }
        """
        raise NotImplementedError()
    
    @staticmethod
    async def extract_keywords(chapter_id: str, top_n: int = 20) -> List[str]:
        """
        提取章节的关键词
        
        Args:
            chapter_id: 章节ID
            top_n: 返回前 N 个关键词
            
        Returns:
            关键词列表
        """
        raise NotImplementedError()
    
    @staticmethod
    async def search_in_file(
        file_id: str,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """
        在文件中搜索关键词
        
        Args:
            file_id: 文件ID
            keyword: 关键词
            
        Returns:
            包含关键词的片段列表 [{'chapter_id': '...', 'text': '...', 'position': int}]
        """
        raise NotImplementedError()


class KBResponse(BaseModel):
    """知识库 API 的统一响应格式"""
    
    success: bool = Field(description="是否成功")
    data: Optional[Any] = Field(default=None, description="响应数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    message: Optional[str] = Field(default=None, description="提示信息")


# ============================================================================
# 实现类（在 backend/core/kb_client.py 中实现这个接口）
# ============================================================================

class KBClientImpl(KBClient):
    """
    知识库客户端的具体实现
    
    这个类在后端实现，通过数据库调用获取数据
    学习/检查/生成 MCP 通过 RPC 调用这个客户端
    """
    pass
