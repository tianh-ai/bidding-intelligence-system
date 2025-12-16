"""
Skill 模板文件
复制此文件开始创建新的 Skill

使用方法:
1. 复制此文件并重命名为具体功能，如: table_extractor.py
2. 修改类名和模型名称
3. 实现 execute() 方法
4. 编写对应的单元测试
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from core.logger import logger


# ========== 输入输出模型 ==========

class TemplateSkillInput(BaseModel):
    """
    Skill 输入参数
    
    使用 Pydantic 强类型验证确保输入安全
    """
    data: str = Field(..., description="输入数据")
    option_a: bool = Field(True, description="选项A")
    option_b: int = Field(10, description="选项B，默认值10")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": "示例数据",
                "option_a": True,
                "option_b": 20
            }
        }


class TemplateSkillOutput(BaseModel):
    """
    Skill 输出结果
    
    标准化输出格式便于调用者使用
    """
    result: str = Field(..., description="处理结果")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="置信度 (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "result": "处理成功",
                "confidence": 0.95,
                "metadata": {"processed_items": 10}
            }
        }


# ========== Skill 实现 ==========

class TemplateSkill:
    """
    Skill 功能描述（一句话总结）
    
    职责:
        - 单一功能实现
        - 无外部依赖（除标准库和 core）
        - 可独立测试
    
    特点:
        - 输入输出使用 Pydantic 强类型验证
        - 完整的错误处理
        - 详细的日志记录
    
    示例:
        >>> skill = TemplateSkill()
        >>> input_data = TemplateSkillInput(data="test")
        >>> output = skill.execute(input_data)
        >>> print(output.result)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Skill
        
        Args:
            config: 可选配置字典，用于自定义行为
        """
        self.config = config or {}
        logger.info(f"{self.__class__.__name__} initialized", extra={"config": self.config})
    
    def execute(self, input_data: TemplateSkillInput) -> TemplateSkillOutput:
        """
        执行 Skill 主逻辑
        
        Args:
            input_data: 输入参数（Pydantic 模型）
        
        Returns:
            TemplateSkillOutput: 处理结果
        
        Raises:
            ValueError: 输入数据无效时
            RuntimeError: 处理失败时
        
        示例:
            >>> skill = TemplateSkill()
            >>> result = skill.execute(TemplateSkillInput(data="test"))
        """
        logger.info(
            f"{self.__class__.__name__} execution started",
            extra={
                "input_data_length": len(input_data.data),
                "option_a": input_data.option_a,
                "option_b": input_data.option_b
            }
        )
        
        try:
            # 1. 验证输入
            if not self.validate(input_data):
                raise ValueError("输入数据验证失败")
            
            # 2. 执行主要逻辑
            # TODO: 在此实现具体功能
            result_text = f"处理完成: {input_data.data}"
            confidence = 0.95
            
            # 3. 构建输出
            output = TemplateSkillOutput(
                result=result_text,
                confidence=confidence,
                metadata={
                    "input_length": len(input_data.data),
                    "option_a_used": input_data.option_a,
                    "option_b_value": input_data.option_b
                }
            )
            
            logger.info(
                f"{self.__class__.__name__} execution completed",
                extra={
                    "result_length": len(output.result),
                    "confidence": output.confidence
                }
            )
            
            return output
            
        except ValueError as e:
            logger.error(f"{self.__class__.__name__} validation error", error=str(e))
            raise
        except Exception as e:
            logger.error(f"{self.__class__.__name__} execution error", error=str(e))
            raise RuntimeError(f"Skill 执行失败: {str(e)}") from e
    
    def validate(self, input_data: TemplateSkillInput) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入参数
        
        Returns:
            bool: 验证是否通过
        
        注意:
            Pydantic 已经进行了类型验证，
            此方法用于业务逻辑验证
        """
        # 业务逻辑验证
        if not input_data.data:
            logger.warning("输入数据为空")
            return False
        
        if input_data.option_b < 0:
            logger.warning("option_b 不能为负数")
            return False
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        返回 Skill 元数据
        
        Returns:
            dict: 包含名称、版本、描述等信息
        """
        return {
            "name": self.__class__.__name__,
            "version": "1.0.0",
            "description": self.__doc__.strip() if self.__doc__ else "无描述",
            "config": self.config
        }


# ========== 使用示例 ==========

if __name__ == "__main__":
    """
    测试 Skill 功能
    
    运行: python -m skills._template_skill
    """
    # 1. 创建 Skill 实例
    skill = TemplateSkill(config={"debug": True})
    
    # 2. 准备输入数据
    input_data = TemplateSkillInput(
        data="测试数据",
        option_a=True,
        option_b=20
    )
    
    # 3. 执行 Skill
    try:
        output = skill.execute(input_data)
        print(f"✅ 执行成功!")
        print(f"   结果: {output.result}")
        print(f"   置信度: {output.confidence}")
        print(f"   元数据: {output.metadata}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 4. 显示 Skill 元数据
    metadata = skill.get_metadata()
    print(f"\n📊 Skill 元数据:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
