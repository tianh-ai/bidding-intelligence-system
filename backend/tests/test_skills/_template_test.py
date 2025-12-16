"""
Skill 单元测试模板
复制此文件开始为新 Skill 编写测试

测试要求:
1. 覆盖率 > 80%
2. 测试正常流程和异常流程
3. 使用 pytest fixtures
4. 清晰的测试文档
"""

import pytest
from pydantic import ValidationError

# 导入要测试的 Skill（修改为实际的 Skill）
from skills._template_skill import (
    TemplateSkill,
    TemplateSkillInput,
    TemplateSkillOutput
)


# ========== Fixtures ==========

@pytest.fixture
def skill():
    """创建 Skill 实例"""
    return TemplateSkill(config={"debug": True})


@pytest.fixture
def valid_input():
    """创建有效的输入数据"""
    return TemplateSkillInput(
        data="测试数据",
        option_a=True,
        option_b=10
    )


@pytest.fixture
def invalid_input():
    """创建无效的输入数据"""
    return TemplateSkillInput(
        data="",  # 空数据
        option_a=False,
        option_b=-5  # 负数
    )


# ========== 基础功能测试 ==========

class TestTemplateSkillBasic:
    """测试 Skill 基础功能"""
    
    def test_initialization(self):
        """测试 Skill 初始化"""
        skill = TemplateSkill()
        assert skill is not None
        assert skill.config == {}
    
    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        config = {"debug": True, "timeout": 30}
        skill = TemplateSkill(config=config)
        assert skill.config == config
    
    def test_get_metadata(self, skill):
        """测试获取元数据"""
        metadata = skill.get_metadata()
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert metadata["name"] == "TemplateSkill"
        assert metadata["version"] == "1.0.0"


# ========== 输入验证测试 ==========

class TestTemplateSkillValidation:
    """测试输入验证功能"""
    
    def test_validate_valid_input(self, skill, valid_input):
        """测试验证有效输入"""
        assert skill.validate(valid_input) == True
    
    def test_validate_empty_data(self, skill):
        """测试验证空数据"""
        input_data = TemplateSkillInput(data="", option_a=True, option_b=10)
        assert skill.validate(input_data) == False
    
    def test_validate_negative_option_b(self, skill):
        """测试验证负数 option_b"""
        input_data = TemplateSkillInput(data="test", option_a=True, option_b=-5)
        assert skill.validate(input_data) == False
    
    def test_pydantic_validation_error(self):
        """测试 Pydantic 类型验证"""
        with pytest.raises(ValidationError):
            # option_b 应该是 int，传入 str 会报错
            TemplateSkillInput(data="test", option_a=True, option_b="invalid")


# ========== 执行逻辑测试 ==========

class TestTemplateSkillExecution:
    """测试 Skill 执行逻辑"""
    
    def test_execute_success(self, skill, valid_input):
        """测试成功执行"""
        output = skill.execute(valid_input)
        
        # 验证输出类型
        assert isinstance(output, TemplateSkillOutput)
        
        # 验证输出字段
        assert output.result is not None
        assert 0.0 <= output.confidence <= 1.0
        assert isinstance(output.metadata, dict)
    
    def test_execute_with_different_options(self, skill):
        """测试不同参数组合"""
        test_cases = [
            {"data": "短", "option_a": True, "option_b": 1},
            {"data": "中等长度的数据", "option_a": False, "option_b": 50},
            {"data": "很长很长很长很长的数据" * 10, "option_a": True, "option_b": 100}
        ]
        
        for case in test_cases:
            input_data = TemplateSkillInput(**case)
            output = skill.execute(input_data)
            assert output.result is not None
            assert output.confidence > 0
    
    def test_execute_with_invalid_input(self, skill, invalid_input):
        """测试执行时输入验证失败"""
        with pytest.raises(ValueError, match="输入数据验证失败"):
            skill.execute(invalid_input)
    
    def test_output_metadata_contains_input_info(self, skill, valid_input):
        """测试输出元数据包含输入信息"""
        output = skill.execute(valid_input)
        
        assert "input_length" in output.metadata
        assert "option_a_used" in output.metadata
        assert "option_b_value" in output.metadata
        assert output.metadata["input_length"] == len(valid_input.data)


# ========== 边界条件测试 ==========

class TestTemplateSkillEdgeCases:
    """测试边界条件和异常情况"""
    
    def test_execute_with_very_long_data(self, skill):
        """测试处理超长数据"""
        long_data = "x" * 100000  # 100KB 数据
        input_data = TemplateSkillInput(data=long_data, option_a=True, option_b=10)
        output = skill.execute(input_data)
        assert output is not None
    
    def test_execute_with_special_characters(self, skill):
        """测试特殊字符处理"""
        special_data = "测试\n换行\t制表符\r回车 emoji😀 符号!@#$%^&*()"
        input_data = TemplateSkillInput(data=special_data, option_a=True, option_b=10)
        output = skill.execute(input_data)
        assert output.result is not None
    
    def test_execute_with_unicode(self, skill):
        """测试 Unicode 字符"""
        unicode_data = "中文 日本語 한국어 العربية Ελληνικά"
        input_data = TemplateSkillInput(data=unicode_data, option_a=True, option_b=10)
        output = skill.execute(input_data)
        assert output.result is not None
    
    def test_execute_with_zero_option_b(self, skill):
        """测试 option_b 为 0 的情况"""
        input_data = TemplateSkillInput(data="test", option_a=True, option_b=0)
        output = skill.execute(input_data)
        assert output is not None
    
    def test_execute_with_max_option_b(self, skill):
        """测试 option_b 的最大值"""
        input_data = TemplateSkillInput(data="test", option_a=True, option_b=999999)
        output = skill.execute(input_data)
        assert output is not None


# ========== 性能测试 ==========

class TestTemplateSkillPerformance:
    """测试性能指标（可选）"""
    
    @pytest.mark.benchmark
    def test_execution_speed(self, skill, benchmark):
        """测试执行速度（需要 pytest-benchmark）"""
        input_data = TemplateSkillInput(data="性能测试数据", option_a=True, option_b=10)
        
        # benchmark 会自动运行多次并统计
        result = benchmark(skill.execute, input_data)
        assert result is not None
    
    def test_multiple_executions(self, skill):
        """测试连续执行稳定性"""
        input_data = TemplateSkillInput(data="连续测试", option_a=True, option_b=10)
        
        # 执行 100 次
        for i in range(100):
            output = skill.execute(input_data)
            assert output.result is not None
            assert output.confidence > 0


# ========== 集成测试 ==========

class TestTemplateSkillIntegration:
    """集成测试（与其他模块交互）"""
    
    def test_skill_with_logger(self, skill, valid_input, caplog):
        """测试日志记录"""
        import logging
        
        with caplog.at_level(logging.INFO):
            skill.execute(valid_input)
        
        # 验证日志记录
        assert "execution started" in caplog.text
        assert "execution completed" in caplog.text
    
    def test_skill_serialization(self, skill, valid_input):
        """测试输入输出序列化"""
        output = skill.execute(valid_input)
        
        # 测试输出可以序列化为 JSON
        output_dict = output.model_dump()
        assert isinstance(output_dict, dict)
        assert "result" in output_dict
        assert "confidence" in output_dict
        
        # 测试输入可以序列化
        input_dict = valid_input.model_dump()
        assert isinstance(input_dict, dict)


# ========== 运行测试 ==========

if __name__ == "__main__":
    """
    直接运行此文件进行测试
    
    命令:
        python -m pytest backend/tests/test_skills/_template_test.py -v
        python -m pytest backend/tests/test_skills/_template_test.py -v --cov=skills --cov-report=html
    """
    pytest.main([__file__, "-v", "--tb=short"])
