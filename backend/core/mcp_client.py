"""
MCP 客户端 - 主程序调用 MCP 服务器的桥接层

提供统一接口让 FastAPI 后端调用 MCP 服务器
"""

import asyncio
import json
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
from core.logger import logger


class MCPClient:
    """MCP 客户端基类"""
    
    def __init__(self, server_name: str, server_path: str):
        """
        初始化 MCP 客户端
        
        Args:
            server_name: MCP 服务器名称
            server_path: MCP 服务器可执行文件路径
        """
        self.server_name = server_name
        self.server_path = Path(server_path)
        
        if not self.server_path.exists():
            raise FileNotFoundError(f"MCP server not found: {server_path}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        process = None
        try:
            # 启动 MCP 服务器
            process = await asyncio.create_subprocess_exec(
                "node",
                str(self.server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 步骤1: 初始化
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "bidding-system", "version": "1.0.0"}
                }
            }
            
            process.stdin.write((json.dumps(init_request) + '\n').encode())
            await process.stdin.drain()
            
            # 读取初始化响应
            init_line = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
            if not init_line:
                raise Exception("No init response")
            
            init_response = json.loads(init_line.decode().strip())
            if "error" in init_response:
                raise Exception(f"Init error: {init_response['error']}")
            
            # 步骤2: 调用工具
            tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            process.stdin.write((json.dumps(tool_request) + '\n').encode())
            await process.stdin.drain()
            
            # 读取工具响应（可能需要较长时间，Python后端执行）
            tool_line = await asyncio.wait_for(process.stdout.readline(), timeout=30.0)
            if not tool_line:
                raise Exception("No tool response")
            
            tool_response = json.loads(tool_line.decode().strip())
            
            if "error" in tool_response:
                raise Exception(f"Tool error: {tool_response['error']}")
            
            # 提取结果
            result = tool_response.get("result", {})
            content = result.get("content", [])
            
            if not content:
                return {}
            
            # 解析返回的 JSON 文本
            text = content[0].get("text", "{}")
            
            # 检查是否是错误
            if content[0].get("type") == "text" and text.startswith("Error:"):
                raise Exception(text)
            
            return json.loads(text)
        except asyncio.TimeoutError:
            logger.error(f"MCP call timeout: {tool_name}")
            if process and process.stderr:
                try:
                    err = await asyncio.wait_for(process.stderr.read(), timeout=0.2)
                    if err:
                        logger.error(f"MCP stderr (timeout): {err.decode(errors='replace').strip()}")
                except Exception:
                    pass
            raise Exception(f"MCP timeout calling {tool_name}")
        except json.JSONDecodeError as e:
            logger.error(f"MCP JSON decode error: {e}")
            if process and process.stderr:
                try:
                    err = await asyncio.wait_for(process.stderr.read(), timeout=0.2)
                    if err:
                        logger.error(f"MCP stderr (json): {err.decode(errors='replace').strip()}")
                except Exception:
                    pass
            raise Exception("Invalid JSON response from MCP")
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            if process and process.stderr:
                try:
                    err = await asyncio.wait_for(process.stderr.read(), timeout=0.2)
                    if err:
                        logger.error(f"MCP stderr: {err.decode(errors='replace').strip()}")
                except Exception:
                    pass
            raise
        finally:
            if process and process.returncode is None:
                try:
                    if process.stdin:
                        process.stdin.close()
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
class KnowledgeBaseMCPClient(MCPClient):
    """知识库 MCP 客户端"""
    
    def __init__(self):
        """初始化知识库 MCP 客户端"""
        # 获取 MCP 服务器路径
        # 兼容两种运行形态：
        # - 本地源码结构：<repo>/backend/core/mcp_client.py 兄弟目录 <repo>/mcp-servers
        # - Docker（compose 挂载 backend 到 /app）：/app/core/mcp_client.py 兄弟目录 /app/mcp-servers
        backend_root = Path(__file__).resolve().parent.parent  # .../backend or /app
        candidate_a = backend_root / "mcp-servers" / "knowledge-base"
        candidate_b = backend_root.parent / "mcp-servers" / "knowledge-base"

        mcp_base = candidate_a if candidate_a.exists() else candidate_b
        server_path = mcp_base / "dist" / "index.js"
        
        super().__init__("knowledge-base", str(server_path))
    
    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """搜索知识库"""
        return await self.call_tool("search_knowledge", {
            "query": query,
            "category": category,
            "limit": limit,
            "min_score": min_score
        })
    
    async def add_knowledge_entry(
        self,
        file_id: str,
        category: str,
        title: str,
        content: str,
        keywords: Optional[List[str]] = None,
        importance_score: float = 50.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """添加知识条目"""
        return await self.call_tool("add_knowledge_entry", {
            "file_id": file_id,
            "category": category,
            "title": title,
            "content": content,
            "keywords": keywords or [],
            "importance_score": importance_score,
            "metadata": metadata or {}
        })
    
    async def get_knowledge_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """获取知识条目"""
        return await self.call_tool("get_knowledge_entry", {
            "entry_id": entry_id
        })
    
    async def list_knowledge_entries(
        self,
        file_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """列出知识条目"""
        return await self.call_tool("list_knowledge_entries", {
            "file_id": file_id,
            "category": category,
            "limit": limit,
            "offset": offset
        })
    
    async def delete_knowledge_entry(self, entry_id: str) -> Dict[str, Any]:
        """删除知识条目"""
        return await self.call_tool("delete_knowledge_entry", {
            "entry_id": entry_id
        })
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return await self.call_tool("get_knowledge_statistics", {})
    
    async def search_knowledge_semantic(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """语义向量搜索"""
        return await self.call_tool("search_knowledge_semantic", {
            "query": query,
            "category": category,
            "limit": limit,
            "min_similarity": min_similarity
        })
    
    async def reindex_embeddings(
        self,
        batch_size: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量重建向量索引"""
        return await self.call_tool("reindex_embeddings", {
            "batch_size": batch_size,
            "category": category
        })


# 全局客户端实例
_kb_client: Optional[KnowledgeBaseMCPClient] = None
_ll_client: Optional['LogicLearningMCPClient'] = None


def get_knowledge_base_client() -> KnowledgeBaseMCPClient:
    """获取知识库 MCP 客户端单例"""
    global _kb_client
    if _kb_client is None:
        _kb_client = KnowledgeBaseMCPClient()
    return _kb_client


class LogicLearningMCPClient(MCPClient):
    """逻辑学习 MCP 客户端"""
    
    def __init__(self):
        """初始化逻辑学习 MCP 客户端"""
        backend_root = Path(__file__).resolve().parent.parent
        candidate_a = backend_root / "mcp-servers" / "logic-learning"
        candidate_b = backend_root.parent / "mcp-servers" / "logic-learning"

        mcp_base = candidate_a if candidate_a.exists() else candidate_b
        server_path = mcp_base / "dist" / "index.js"
        
        super().__init__("logic-learning", str(server_path))
    
    async def start_learning(
        self,
        file_ids: List[str],
        learning_type: str,
        chapter_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """启动学习任务"""
        return await self.call_tool("start_learning", {
            "file_ids": file_ids,
            "learning_type": learning_type,
            "chapter_ids": chapter_ids or []
        })
    
    async def get_learning_status(self, task_id: str) -> Dict[str, Any]:
        """查询学习任务状态"""
        return await self.call_tool("get_learning_status", {
            "task_id": task_id
        })
    
    async def get_learning_result(self, task_id: str) -> Dict[str, Any]:
        """获取学习任务结果"""
        return await self.call_tool("get_learning_result", {
            "task_id": task_id
        })
    
    async def get_logic_database(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取逻辑数据库统计"""
        return await self.call_tool("get_logic_database", {
            "category": category
        })


def get_logic_learning_client() -> LogicLearningMCPClient:
    """获取逻辑学习 MCP 客户端单例"""
    global _ll_client
    if _ll_client is None:
        _ll_client = LogicLearningMCPClient()
    return _ll_client


# 使用示例
async def example_usage():
    """使用示例"""
    client = get_knowledge_base_client()
    
    # 搜索知识
    results = await client.search_knowledge("投标要求", category="tender", limit=5)
    print(f"搜索结果: {len(results)} 条")
    
    # 添加知识条目
    entry = await client.add_knowledge_entry(
        file_id="test-file-id",
        category="tender",
        title="测试知识条目",
        content="这是一个测试内容",
        keywords=["测试", "示例"],
        importance_score=80.0
    )
    print(f"已添加: {entry}")
    
    # 获取统计
    stats = await client.get_statistics()
    print(f"统计信息: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())
