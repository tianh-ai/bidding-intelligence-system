"""知识库路由 - 通过 MCP 客户端调用知识库服务

按项目要求：只允许通过 MCP 访问知识库（不做 DB 直连降级）。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from core.mcp_client import get_knowledge_base_client
from core.logger import logger

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ========== 请求模型 ==========

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    category: Optional[str] = None
    limit: int = 10
    min_score: float = 0.0


class AddEntryRequest(BaseModel):
    """添加条目请求"""
    file_id: str
    category: str
    title: str
    content: str
    keywords: Optional[List[str]] = None
    importance_score: float = 50.0
    metadata: Optional[Dict[str, Any]] = None


class ListRequest(BaseModel):
    """列表请求"""
    file_id: Optional[str] = None
    category: Optional[str] = None
    limit: int = 50
    offset: int = 0


class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""
    query: str
    category: Optional[str] = None
    limit: int = 10
    min_similarity: float = 0.7


class ReindexRequest(BaseModel):
    """重建索引请求"""
    batch_size: int = 10
    category: Optional[str] = None


# ========== API 端点 ==========

@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """
    搜索知识库
    
    POST /api/knowledge/search
    Body: {
        "query": "投标要求",
        "category": "tender",
        "limit": 10,
        "min_score": 0.0
    }
    """
    try:
        client = get_knowledge_base_client()
        results = await client.search_knowledge(
            query=request.query,
            category=request.category,
            limit=request.limit,
            min_score=request.min_score,
        )
        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "total": len(results),
            "source": "mcp",
        }
    except Exception as e:
        logger.error(f"MCP 搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entries")
async def add_entry(request: AddEntryRequest):
    """
    添加知识条目
    
    POST /api/knowledge/entries
    Body: {
        "file_id": "file-123",
        "category": "tender",
        "title": "项目要求",
        "content": "...",
        "keywords": ["投标", "要求"],
        "importance_score": 80.0
    }
    """
    try:
        client = get_knowledge_base_client()
        result = await client.add_knowledge_entry(
            file_id=request.file_id,
            category=request.category,
            title=request.title,
            content=request.content,
            keywords=request.keywords,
            importance_score=request.importance_score,
            metadata=request.metadata,
        )
        return {"status": "success", **result, "source": "mcp"}
    except Exception as e:
        logger.error(f"MCP 添加知识条目失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{entry_id}")
async def get_entry(entry_id: str):
    """
    获取知识条目详情
    
    GET /api/knowledge/entries/{entry_id}
    """
    try:
        client = get_knowledge_base_client()
        result = await client.get_knowledge_entry(entry_id)
        if not result:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return {"status": "success", "entry": result, "source": "mcp"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP 获取知识条目失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entries/list")
async def list_entries(request: ListRequest):
    """
    列出知识条目
    
    POST /api/knowledge/entries/list
    Body: {
        "file_id": "file-123",  // 可选
        "category": "tender",   // 可选
        "limit": 50,
        "offset": 0
    }
    """
    try:
        client = get_knowledge_base_client()
        result = await client.list_knowledge_entries(
            file_id=request.file_id,
            category=request.category,
            limit=request.limit,
            offset=request.offset,
        )
        return {"status": "success", **result, "source": "mcp"}
    except Exception as e:
        logger.error(f"MCP 列出知识条目失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str):
    """
    删除知识条目
    
    DELETE /api/knowledge/entries/{entry_id}
    """
    try:
        client = get_knowledge_base_client()
        result = await client.delete_knowledge_entry(entry_id)
        return {"status": "success", **result, "source": "mcp"}
    except Exception as e:
        logger.error(f"MCP 删除知识条目失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """
    获取知识库统计信息
    
    GET /api/knowledge/statistics
    """
    try:
        client = get_knowledge_base_client()
        result = await client.get_statistics()
        return {"status": "success", **result, "source": "mcp"}
    except Exception as e:
        logger.error(f"MCP 获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    健康检查 - 检查 MCP 服务器是否可用
    
    GET /api/knowledge/health
    """
    try:
        client = get_knowledge_base_client()
        await client.get_statistics()
        return {"status": "healthy", "mode": "mcp", "message": "Knowledge Base MCP server is running"}
    except Exception as e:
        logger.error(f"MCP 健康检查失败: {e}", exc_info=True)
        return {"status": "unhealthy", "mode": "mcp", "message": str(e)}


@router.post("/search/semantic")
async def search_semantic(request: SemanticSearchRequest):
    """
    语义向量搜索（使用 Ollama embeddings）
    
    POST /api/knowledge/search/semantic
    Body: {
        "query": "项目经理需要什么资质？",
        "category": "tender",
        "limit": 10,
        "min_similarity": 0.7
    }
    """
    try:
        client = get_knowledge_base_client()
        results = await client.search_knowledge_semantic(
            query=request.query,
            category=request.category,
            limit=request.limit,
            min_similarity=request.min_similarity,
        )
        return {
            "status": "success",
            "query": request.query,
            "search_type": "semantic",
            "results": results,
            "total": len(results),
            "source": "mcp",
        }
    except Exception as e:
        logger.error(f"MCP 语义搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_embeddings(request: ReindexRequest):
    """
    批量重建向量索引
    
    POST /api/knowledge/reindex
    Body: {
        "batch_size": 10,
        "category": "tender"  // 可选
    }
    """
    try:
        client = get_knowledge_base_client()
        result = await client.reindex_embeddings(batch_size=request.batch_size, category=request.category)
        return {"status": "success", **result, "source": "mcp"}
    except Exception as e:
        logger.error(f"MCP 重建索引失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
