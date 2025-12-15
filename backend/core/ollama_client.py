"""
Ollama 客户端 - 本地 LLM 和 Embeddings
支持文本嵌入生成和聊天补全
"""

import httpx
from typing import List, Dict, Any, Optional
from core.logger import logger
from core.config import get_settings


class OllamaClient:
    """Ollama 本地模型客户端"""
    
    def __init__(self):
        """初始化 Ollama 客户端"""
        settings = get_settings()
        self.base_url = settings.OLLAMA_BASE_URL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.chat_model = settings.OLLAMA_CHAT_MODEL
        self.timeout = 60.0  # 本地模型超时时间
        
        logger.info(f"Ollama client initialized: {self.base_url}")
        logger.info(f"Embedding model: {self.embedding_model}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            向量嵌入列表（通常是 768 或 1024 维）
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                result = response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise ValueError("Ollama returned empty embedding")
                
                logger.debug(f"Generated embedding: {len(embedding)} dimensions")
                return embedding
                
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise Exception(f"Failed to generate embedding: {e}")
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成向量嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            向量嵌入列表
        """
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        聊天补全
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称（默认使用配置的模型）
            stream: 是否流式输出
            
        Returns:
            模型回复文本
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model or self.chat_model,
                        "messages": messages,
                        "stream": stream
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                return result.get("message", {}).get("content", "")
                
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise
    
    async def check_health(self) -> bool:
        """
        检查 Ollama 服务健康状态
        
        Returns:
            是否健康
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                logger.info("Ollama service is healthy")
                return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        列出可用模型
        
        Returns:
            模型名称列表
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                result = response.json()
                models = [model["name"] for model in result.get("models", [])]
                logger.info(f"Available models: {models}")
                return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


# 全局单例
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """获取 Ollama 客户端单例"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


# 使用示例
async def example_usage():
    """使用示例"""
    client = get_ollama_client()
    
    # 检查健康状态
    is_healthy = await client.check_health()
    print(f"Ollama healthy: {is_healthy}")
    
    # 生成向量
    embedding = await client.generate_embedding("这是一个测试文本")
    print(f"Embedding dimensions: {len(embedding)}")
    
    # 聊天
    response = await client.chat([
        {"role": "user", "content": "你好，介绍一下你自己"}
    ])
    print(f"Response: {response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
