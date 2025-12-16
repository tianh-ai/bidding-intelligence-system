"""
Skills Package
独立的功能模块集合，提供可复用的纯函数实现

特点:
- 独立性: 每个 Skill 可单独使用
- 可测试性: 完整的单元测试覆盖
- 类型安全: Pydantic 强类型验证
- 无外部依赖: 仅依赖标准库和 core 模块

使用示例:
    from skills.table_extractor import TableExtractor
    
    extractor = TableExtractor()
    result = extractor.execute(input_data)
"""

__version__ = "1.0.0"
__all__ = [
    "table_extractor",
]
