"""
FormatConverter Skill - 格式转换和标准化

功能：
1. 单位转换（EMU → CM, PT, Inches等）
2. 字体大小转换和标准化
3. 颜色格式转换（RGB, HEX, HSL）
4. 日期时间格式标准化
5. 文本格式清理和标准化

版本：1.0.0
"""

import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re
from core.logger import logger


class FormatConverterInput(BaseModel):
    """格式转换输入模型"""
    
    value: Union[int, float, str, List, tuple]  # 支持list和tuple（用于RGB等）
    conversion_type: str = Field(..., description="转换类型: emu_to_cm, emu_to_pt, font_size, rgb_to_hex, date_normalize, text_clean")
    source_unit: Optional[str] = Field(None, description="源单位（可选）")
    target_unit: Optional[str] = Field(None, description="目标单位（可选）")
    options: Dict[str, Any] = Field(default_factory=dict, description="转换选项")
    
    @validator('conversion_type')
    def validate_conversion_type(cls, v):
        """验证转换类型"""
        valid_types = [
            'emu_to_cm', 'emu_to_pt', 'emu_to_inches',
            'font_size', 'rgb_to_hex', 'hex_to_rgb',
            'date_normalize', 'text_clean', 'number_format'
        ]
        if v not in valid_types:
            raise ValueError(f"不支持的转换类型: {v}. 有效类型: {', '.join(valid_types)}")
        return v


class FormatConverterOutput(BaseModel):
    """格式转换输出模型"""
    
    original_value: Union[int, float, str, List, tuple]
    converted_value: Union[int, float, str, List, Dict]
    conversion_type: str
    source_unit: Optional[str] = None
    target_unit: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FormatConverter:
    """
    格式转换Skill
    
    提供各种格式转换功能，从engines/format_extractor.py提取的转换逻辑
    """
    
    # 单位转换常量
    EMU_PER_INCH = 914400  # 1 inch = 914400 EMU
    EMU_PER_PT = 12700     # 1 pt = 12700 EMU
    CM_PER_INCH = 2.54     # 1 inch = 2.54 cm
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化FormatConverter
        
        Args:
            config: 配置字典（可选）
        """
        self.config = config or {}
        logger.info("FormatConverter initialized")
    
    def execute(self, input_data: FormatConverterInput) -> FormatConverterOutput:
        """
        执行格式转换
        
        Args:
            input_data: 转换输入数据
            
        Returns:
            FormatConverterOutput: 转换结果
        """
        try:
            # 根据转换类型调用相应方法
            conversion_map = {
                'emu_to_cm': self._emu_to_cm,
                'emu_to_pt': self._emu_to_pt,
                'emu_to_inches': self._emu_to_inches,
                'font_size': self._convert_font_size,
                'rgb_to_hex': self._rgb_to_hex,
                'hex_to_rgb': self._hex_to_rgb,
                'date_normalize': self._normalize_date,
                'text_clean': self._clean_text,
                'number_format': self._format_number,
            }
            
            converter_func = conversion_map.get(input_data.conversion_type)
            if not converter_func:
                raise ValueError(f"未找到转换函数: {input_data.conversion_type}")
            
            # 执行转换
            converted_value = converter_func(input_data.value, input_data.options)
            
            return FormatConverterOutput(
                original_value=input_data.value,
                converted_value=converted_value,
                conversion_type=input_data.conversion_type,
                source_unit=input_data.source_unit,
                target_unit=input_data.target_unit,
                success=True,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0"
                }
            )
            
        except Exception as e:
            logger.error(f"格式转换失败: {e}")
            return FormatConverterOutput(
                original_value=input_data.value,
                converted_value=input_data.value,  # 返回原值
                conversion_type=input_data.conversion_type,
                success=False,
                error=str(e)
            )
    
    def _emu_to_cm(self, value: Union[int, float], options: Dict) -> Optional[float]:
        """
        将EMU单位转换为厘米
        
        Args:
            value: EMU值
            options: 转换选项（如precision）
            
        Returns:
            厘米值（保留2位小数）
        """
        if value is None or value == 0:
            return None
        
        try:
            inches = value / self.EMU_PER_INCH
            cm = inches * self.CM_PER_INCH
            precision = options.get('precision', 2)
            return round(cm, precision)
        except Exception as e:
            logger.warning(f"EMU转CM失败: {e}")
            return None
    
    def _emu_to_pt(self, value: Union[int, float], options: Dict) -> Optional[float]:
        """
        将EMU单位转换为磅（pt）
        
        Args:
            value: EMU值
            options: 转换选项
            
        Returns:
            磅值（保留1位小数）
        """
        if value is None or value == 0:
            return None
        
        try:
            pt = value / self.EMU_PER_PT
            precision = options.get('precision', 1)
            return round(pt, precision)
        except Exception as e:
            logger.warning(f"EMU转PT失败: {e}")
            return None
    
    def _emu_to_inches(self, value: Union[int, float], options: Dict) -> Optional[float]:
        """
        将EMU单位转换为英寸
        
        Args:
            value: EMU值
            options: 转换选项
            
        Returns:
            英寸值
        """
        if value is None or value == 0:
            return None
        
        try:
            inches = value / self.EMU_PER_INCH
            precision = options.get('precision', 2)
            return round(inches, precision)
        except Exception as e:
            logger.warning(f"EMU转Inches失败: {e}")
            return None
    
    def _convert_font_size(self, value: Any, options: Dict) -> Optional[float]:
        """
        转换字体大小为磅
        
        Args:
            value: 字体大小（可能是Pt对象或数字）
            options: 转换选项
            
        Returns:
            磅值
        """
        if value is None:
            return None
        
        try:
            # 如果是Pt对象（from docx.shared import Pt）
            if hasattr(value, 'pt'):
                pt_value = value.pt
            # 如果是EMU值
            elif isinstance(value, (int, float)) and value > 1000:
                pt_value = value / self.EMU_PER_PT
            # 直接是磅值
            else:
                pt_value = float(value)
            
            precision = options.get('precision', 1)
            return round(pt_value, precision)
        except Exception as e:
            logger.warning(f"字体大小转换失败: {e}")
            return None
    
    def _rgb_to_hex(self, value: Union[str, List, tuple], options: Dict) -> str:
        """
        RGB颜色转十六进制
        
        Args:
            value: RGB值（"255,0,0" 或 [255,0,0] 或 (255,0,0)）
            options: 转换选项
            
        Returns:
            十六进制颜色值（如 "#FF0000"）
        """
        try:
            if isinstance(value, str):
                rgb = [int(x.strip()) for x in value.split(',')]
            else:
                rgb = list(value)
            
            if len(rgb) != 3:
                raise ValueError("RGB值必须包含3个分量")
            
            hex_value = '#{:02X}{:02X}{:02X}'.format(rgb[0], rgb[1], rgb[2])
            
            if options.get('lowercase', False):
                hex_value = hex_value.lower()
            
            return hex_value
        except Exception as e:
            logger.warning(f"RGB转HEX失败: {e}")
            return "#000000"
    
    def _hex_to_rgb(self, value: str, options: Dict) -> List[int]:
        """
        十六进制颜色转RGB
        
        Args:
            value: 十六进制颜色值（如 "#FF0000" 或 "FF0000"）
            options: 转换选项
            
        Returns:
            RGB列表 [R, G, B]
        """
        try:
            hex_str = value.lstrip('#')
            if len(hex_str) != 6:
                raise ValueError("HEX颜色值长度必须为6")
            
            rgb = [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]
            
            if options.get('normalized', False):
                # 返回0-1之间的归一化值
                rgb = [x/255.0 for x in rgb]
            
            return rgb
        except Exception as e:
            logger.warning(f"HEX转RGB失败: {e}")
            return [0, 0, 0]
    
    def _normalize_date(self, value: str, options: Dict) -> str:
        """
        标准化日期格式
        
        Args:
            value: 日期字符串（支持多种格式）
            options: 转换选项（如output_format）
            
        Returns:
            标准化的日期字符串
        """
        try:
            # 常见日期格式模式
            date_patterns = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y%m%d',
            ]
            
            parsed_date = None
            for pattern in date_patterns:
                try:
                    parsed_date = datetime.strptime(value.strip(), pattern)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                raise ValueError(f"无法解析日期: {value}")
            
            # 输出格式
            output_format = options.get('output_format', '%Y-%m-%d')
            return parsed_date.strftime(output_format)
            
        except Exception as e:
            logger.warning(f"日期标准化失败: {e}")
            return value
    
    def _clean_text(self, value: str, options: Dict) -> str:
        """
        清理和标准化文本
        
        Args:
            value: 原始文本
            options: 清理选项
                - remove_extra_spaces: 删除多余空格（默认True）
                - remove_newlines: 删除换行符（默认False）
                - strip: 去除首尾空白（默认True）
                - normalize_punctuation: 标准化标点（默认False）
            
        Returns:
            清理后的文本
        """
        try:
            text = str(value)
            
            # 去除首尾空白
            if options.get('strip', True):
                text = text.strip()
            
            # 删除多余空格
            if options.get('remove_extra_spaces', True):
                text = re.sub(r'\s+', ' ', text)
            
            # 删除换行符
            if options.get('remove_newlines', False):
                text = text.replace('\n', ' ').replace('\r', '')
            
            # 标准化标点
            if options.get('normalize_punctuation', False):
                # 统一中文标点
                punctuation_map = {
                    '，': ',',
                    '。': '.',
                    '；': ';',
                    '：': ':',
                    '！': '!',
                    '？': '?',
                    '（': '(',
                    '）': ')',
                    '【': '[',
                    '】': ']',
                }
                for cn, en in punctuation_map.items():
                    text = text.replace(cn, en)
            
            return text
            
        except Exception as e:
            logger.warning(f"文本清理失败: {e}")
            return value
    
    def _format_number(self, value: Union[int, float, str], options: Dict) -> str:
        """
        格式化数字
        
        Args:
            value: 数字值
            options: 格式化选项
                - decimals: 小数位数（默认2）
                - thousands_separator: 千位分隔符（默认','）
                - prefix: 前缀（如'￥'）
                - suffix: 后缀（如'元'）
            
        Returns:
            格式化的数字字符串
        """
        try:
            num = float(value)
            decimals = options.get('decimals', 2)
            
            # 格式化小数
            formatted = f"{num:,.{decimals}f}"
            
            # 自定义千位分隔符
            sep = options.get('thousands_separator', ',')
            if sep != ',':
                formatted = formatted.replace(',', sep)
            
            # 添加前缀和后缀
            prefix = options.get('prefix', '')
            suffix = options.get('suffix', '')
            
            return f"{prefix}{formatted}{suffix}"
            
        except Exception as e:
            logger.warning(f"数字格式化失败: {e}")
            return str(value)
    
    def validate(self, input_data: FormatConverterInput) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            是否有效
        """
        try:
            # Pydantic已经在模型级别验证了
            # 这里可以添加额外的业务逻辑验证
            
            if input_data.value is None:
                logger.warning("输入值为None")
                return False
            
            # 特定类型的验证
            if 'rgb' in input_data.conversion_type:
                # RGB转换需要特定格式
                pass
            
            return True
        except Exception as e:
            logger.error(f"验证失败: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取Skill元数据
        
        Returns:
            元数据字典
        """
        return {
            "name": "FormatConverter",
            "version": "1.0.0",
            "description": "格式转换和标准化Skill",
            "supported_conversions": [
                "emu_to_cm", "emu_to_pt", "emu_to_inches",
                "font_size", "rgb_to_hex", "hex_to_rgb",
                "date_normalize", "text_clean", "number_format"
            ],
            "author": "Bidding Intelligence System",
            "created_at": "2025-12-16"
        }


# 便捷函数
def convert_format(
    value: Union[int, float, str],
    conversion_type: str,
    **options
) -> Union[int, float, str, Dict]:
    """
    便捷的格式转换函数
    
    Args:
        value: 要转换的值
        conversion_type: 转换类型
        **options: 转换选项
        
    Returns:
        转换后的值
    """
    converter = FormatConverter()
    input_data = FormatConverterInput(
        value=value,
        conversion_type=conversion_type,
        options=options
    )
    result = converter.execute(input_data)
    return result.converted_value if result.success else value


# 示例用法
if __name__ == '__main__':
    # 测试EMU转换
    print("=== EMU转换测试 ===")
    print(f"914400 EMU = {convert_format(914400, 'emu_to_cm')} cm")
    print(f"12700 EMU = {convert_format(12700, 'emu_to_pt')} pt")
    
    # 测试颜色转换
    print("\n=== 颜色转换测试 ===")
    print(f"RGB(255,0,0) = {convert_format([255, 0, 0], 'rgb_to_hex')}")
    print(f"#FF0000 = {convert_format('#FF0000', 'hex_to_rgb')}")
    
    # 测试文本清理
    print("\n=== 文本清理测试 ===")
    text = "  这是    一段   文本  \n\n  "
    print(f"原文: '{text}'")
    print(f"清理后: '{convert_format(text, 'text_clean')}'")
    
    # 测试数字格式化
    print("\n=== 数字格式化测试 ===")
    print(f"1234567.89 = {convert_format(1234567.89, 'number_format', decimals=2, prefix='￥')}")
