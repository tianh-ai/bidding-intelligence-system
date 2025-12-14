"""
文档总结路由
提供链接、文件、文件夹的智能总结功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup
from core.logger import logger
from database import db
import os

router = APIRouter()


class SummarizeLinkRequest(BaseModel):
    """链接总结请求"""
    url: str


class SummarizeFileRequest(BaseModel):
    """文件总结请求"""
    fileId: str


class SummarizeFolderRequest(BaseModel):
    """文件夹总结请求"""
    folderPath: str


@router.post("/summary/link")
async def summarize_link(request: SummarizeLinkRequest):
    """
    总结招标公告链接
    
    Args:
        request: 包含URL的请求
        
    Returns:
        总结内容
    """
    try:
        logger.info(f"📄 开始总结链接: {request.url}")
        
        # 获取网页内容
        response = requests.get(request.url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 提取主要文本内容
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 获取文本
        text = soup.get_text(separator='\n', strip=True)
        
        # 简单的总结逻辑（这里可以接入LLM进行智能总结）
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content = '\n'.join(lines[:50])  # 取前50行作为摘要
        
        summary = f"""# 链接内容摘要

**来源：** {request.url}

## 主要内容

{content}

---
*注：这是自动提取的内容摘要，如需更详细的分析请使用完整文档总结功能。*
"""
        
        return {
            "status": "success",
            "summary": summary,
            "url": request.url
        }
        
    except requests.RequestException as e:
        logger.error(f"获取链接内容失败: {e}")
        raise HTTPException(status_code=400, detail=f"无法访问链接: {str(e)}")
    except Exception as e:
        logger.error(f"链接总结失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"总结失败: {str(e)}")


@router.post("/summary/file")
async def summarize_file(request: SummarizeFileRequest):
    """
    总结已上传的文件
    
    Args:
        request: 包含文件ID的请求
        
    Returns:
        总结内容
    """
    try:
        logger.info(f"📄 开始总结文件: {request.fileId}")
        
        # 从数据库获取文件信息
        file_info = db.query_one(
            "SELECT id, filename, filetype, archive_path FROM uploaded_files WHERE id = %s",
            (request.fileId,)
        )
        
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        filename = file_info.get("filename", "未知文件")
        
        # 从数据库获取文件的章节信息
        chapters = db.query(
            """
            SELECT chapter_number, chapter_title, content 
            FROM chapters 
            WHERE file_id = %s 
            ORDER BY position_order
            LIMIT 10
            """,
            (request.fileId,)
        )
        
        if not chapters:
            return {
                "status": "success",
                "summary": f"# 文件摘要\n\n**文件名：** {filename}\n\n*此文件暂无解析内容，请先进行文档解析。*",
                "fileId": request.fileId
            }
        
        # 生成摘要
        chapter_list = []
        for ch in chapters:
            chapter_list.append(
                f"### {ch.get('chapter_number', '')} {ch.get('chapter_title', '未命名章节')}\n\n"
                f"{ch.get('content', '')[:200]}...\n"
            )
        
        summary = f"""# 文件摘要

**文件名：** {filename}
**章节数：** {len(chapters)}

## 内容概览

{''.join(chapter_list)}

---
*注：仅显示前10个章节的部分内容。*
"""
        
        return {
            "status": "success",
            "summary": summary,
            "fileId": request.fileId,
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件总结失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"总结失败: {str(e)}")


@router.post("/summary/folder")
async def summarize_folder(request: SummarizeFolderRequest):
    """
    总结文件夹中的所有文件
    
    Args:
        request: 包含文件夹路径的请求
        
    Returns:
        总结内容
    """
    try:
        logger.info(f"📁 开始总结文件夹: {request.folderPath}")
        
        # 检查文件夹是否存在
        if not os.path.exists(request.folderPath):
            raise HTTPException(status_code=404, detail="文件夹不存在")
        
        if not os.path.isdir(request.folderPath):
            raise HTTPException(status_code=400, detail="路径不是文件夹")
        
        # 列出文件夹中的文件
        files = []
        for filename in os.listdir(request.folderPath):
            file_path = os.path.join(request.folderPath, filename)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                files.append({
                    "name": filename,
                    "size": size,
                    "path": file_path
                })
        
        # 生成摘要
        file_list = []
        for f in files[:20]:  # 只列出前20个文件
            size_mb = f['size'] / (1024 * 1024)
            file_list.append(f"- **{f['name']}** ({size_mb:.2f} MB)")
        
        summary = f"""# 文件夹摘要

**路径：** {request.folderPath}
**文件总数：** {len(files)}

## 文件列表

{chr(10).join(file_list)}

{f'*（仅显示前20个文件）*' if len(files) > 20 else ''}
"""
        
        return {
            "status": "success",
            "summary": summary,
            "folderPath": request.folderPath,
            "totalFiles": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件夹总结失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"总结失败: {str(e)}")


@router.get("/summary/history")
async def get_summary_history(page: int = 1, limit: int = 20):
    """
    获取总结历史（这里返回空列表，可以后续扩展）
    
    Args:
        page: 页码
        limit: 每页数量
        
    Returns:
        历史记录列表
    """
    return {
        "status": "success",
        "data": [],
        "total": 0,
        "page": page,
        "limit": limit
    }
