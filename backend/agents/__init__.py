"""
三层代理架构
Layer 1: 预处理代理（Preprocessor Agent）
Layer 2: 约束提取代理（Constraint Extractor Agent）
Layer 3: 策略生成代理（Strategy Generator Agent）
"""

from .preprocessor import PreprocessorAgent
from .constraint_extractor import ConstraintExtractorAgent
# from .strategy_generator import StrategyGeneratorAgent  # 阶段2实施

__all__ = [
    "PreprocessorAgent",
    "ConstraintExtractorAgent",
    # "StrategyGeneratorAgent",
]
