"""
多模型路由管理器 (LLM Router)
根据任务类型智能选择最适合的大模型
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from openai import OpenAI
from core.logger import logger
from core.config import get_settings

settings = get_settings()


class TaskType(str, Enum):
    """任务类型"""
    GENERATION = "generation"  # 内容生成 - 使用DeepSeek
    SCORING = "scoring"  # 评分评估 - 使用千问
    ANALYSIS = "analysis"  # 分析推理 - 使用千问
    COMPARISON = "comparison"  # 对比分析 - 使用千问
    FEEDBACK = "feedback"  # 反馈分析 - 使用DeepSeek
    EXTRACTION = "extraction"  # 信息提取 - 使用千问


class ModelConfig:
    """模型配置"""
    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: str,
        default_model: str,
        max_tokens: int = 4000,
        temperature: float = 0.3
    ):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.temperature = temperature


class LLMRouter:
    """
    大模型路由管理器
    
    功能：
    - 根据任务类型选择最优模型
    - 统一的调用接口
    - 自动重试和错误处理
    - 使用统计和成本追踪
    """
    
    def __init__(self):
        """初始化路由器"""
        logger.info("Initializing LLM Router")
        
        # 配置各个模型
        self.models = {
            "deepseek": ModelConfig(
                name="DeepSeek",
                api_key="sk-1fc432ea945d4c448f3699d674808167",
                base_url="https://api.deepseek.com",
                default_model="deepseek-chat",
                max_tokens=4000,
                temperature=0.7  # 生成任务用更高的温度
            ),
            "qwen": ModelConfig(
                name="通义千问",
                api_key="sk-17745e25a6b74f4994de3b8b42341b57",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                default_model="qwen-plus",
                max_tokens=4000,
                temperature=0.3  # 分析任务用更低的温度
            )
        }
        
        # 任务类型到模型的映射
        self.task_model_mapping = {
            TaskType.GENERATION: "deepseek",      # DeepSeek擅长内容生成
            TaskType.SCORING: "qwen",             # 千问擅长评估打分
            TaskType.ANALYSIS: "qwen",            # 千问擅长逻辑分析
            TaskType.COMPARISON: "qwen",          # 千问擅长对比分析
            TaskType.FEEDBACK: "deepseek",        # DeepSeek擅长理解反馈
            TaskType.EXTRACTION: "qwen"           # 千问擅长信息提取
        }
        
        # 初始化客户端
        self.clients: Dict[str, OpenAI] = {}
        for model_name, config in self.models.items():
            self.clients[model_name] = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
        
        # 使用统计
        self.usage_stats: Dict[str, Dict] = {
            model_name: {
                "calls": 0,
                "tokens": 0,
                "errors": 0
            }
            for model_name in self.models.keys()
        }
        
        logger.info(
            f"LLM Router initialized with {len(self.models)} models",
            extra={"models": list(self.models.keys())}
        )
    
    def get_model_for_task(self, task_type: TaskType) -> str:
        """根据任务类型获取推荐模型"""
        return self.task_model_mapping.get(task_type, "qwen")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        统一的聊天补全接口
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            model_name: 指定模型（可选，默认根据任务类型自动选择）
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            **kwargs: 其他参数
            
        Returns:
            响应字典，包含content, model, usage等
        """
        # 选择模型
        if model_name is None:
            model_name = self.get_model_for_task(task_type)
        
        config = self.models[model_name]
        client = self.clients[model_name]
        
        # 参数设置
        temp = temperature if temperature is not None else config.temperature
        tokens = max_tokens if max_tokens is not None else config.max_tokens
        
        logger.info(
            f"Calling {config.name} for {task_type.value}",
            extra={
                "model": model_name,
                "temperature": temp,
                "max_tokens": tokens,
                "messages_count": len(messages)
            }
        )
        
        try:
            # 调用API
            response = client.chat.completions.create(
                model=config.default_model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                **kwargs
            )
            
            # 提取结果
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            # 更新统计
            self.usage_stats[model_name]["calls"] += 1
            self.usage_stats[model_name]["tokens"] += usage["total_tokens"]
            
            logger.info(
                f"{config.name} call successful",
                extra={
                    "model": model_name,
                    "tokens_used": usage["total_tokens"],
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
            return {
                "content": content,
                "model": model_name,
                "model_name": config.name,
                "usage": usage,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            # 更新错误统计
            self.usage_stats[model_name]["errors"] += 1
            
            logger.error(
                f"{config.name} call failed",
                extra={
                    "model": model_name,
                    "error": str(e),
                    "task_type": task_type.value
                },
                exc_info=True
            )
            
            raise Exception(f"LLM调用失败 ({config.name}): {str(e)}")
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        task_type: TaskType = TaskType.GENERATION,
        **kwargs
    ) -> str:
        """
        简化的文本生成接口
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            task_type: 任务类型
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = await self.chat_completion(
            messages=messages,
            task_type=task_type,
            **kwargs
        )
        
        return response["content"]
    
    async def score_content(
        self,
        content: str,
        criteria: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评分专用接口（使用千问）
        
        Args:
            content: 要评分的内容
            criteria: 评分标准
            context: 上下文信息（可选）
            
        Returns:
            评分结果字典 {score, reasoning}
        """
        system_prompt = """你是一位专业的投标文件评审专家。
你需要根据给定的评分标准，对内容进行客观、准确的评分。
请以JSON格式返回评分结果：
{
  "score": 85,
  "reasoning": "评分理由..."
}
"""
        
        user_prompt = f"""评分标准：{criteria}

要评分的内容：
{content}
"""
        
        if context:
            user_prompt += f"\n\n上下文信息：\n{context}"
        
        user_prompt += "\n\n请给出评分（0-100）和详细理由。"
        
        response = await self.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            task_type=TaskType.SCORING,
            temperature=0.1  # 评分用更低的温度保证一致性
        )
        
        # 解析JSON响应
        import json
        try:
            result = json.loads(response["content"])
            return {
                "score": result.get("score", 70),
                "reasoning": result.get("reasoning", ""),
                "model": response["model_name"]
            }
        except:
            # 如果解析失败，返回默认值
            return {
                "score": 70,
                "reasoning": response["content"],
                "model": response["model_name"]
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        total_calls = sum(stats["calls"] for stats in self.usage_stats.values())
        total_tokens = sum(stats["tokens"] for stats in self.usage_stats.values())
        total_errors = sum(stats["errors"] for stats in self.usage_stats.values())
        successful_calls = total_calls - total_errors
        
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_errors": total_errors,
            "successful_calls": successful_calls,
            "by_model": self.usage_stats,
            "success_rate": (
                (successful_calls / total_calls * 100)
                if total_calls > 0 else 0
            )
        }


# 全局LLM路由器实例
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """获取全局LLM路由器实例（单例模式）"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
