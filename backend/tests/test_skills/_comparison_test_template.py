"""
新旧实现对比测试模板
用于验证 Skill 迁移后功能一致性

使用场景:
    从旧 Engine/Agent 迁移到新 Skill 时，
    确保新实现的输出与旧实现完全一致

使用方法:
    1. 复制此文件并重命名为: test_comparison_{skill_name}.py
    2. 修改 OLD_IMPLEMENTATION 和 NEW_IMPLEMENTATION
    3. 实现 prepare_test_data() 准备测试数据
    4. 运行测试验证一致性
"""

import pytest
from typing import List, Dict, Any, Tuple
from pathlib import Path


# ========== 配置区域 ==========

# TODO: 修改为实际的导入
# 旧实现示例:
# from engines.parse_engine import HybridParseEngine as OLD_IMPLEMENTATION

# 新实现示例:
# from skills.table_extractor import TableExtractor as NEW_IMPLEMENTATION

# 模拟导入（替换为实际实现）
class OLD_IMPLEMENTATION:
    """旧实现占位符"""
    def extract(self, file_path: str) -> Dict[str, Any]:
        return {"data": "old result"}


class NEW_IMPLEMENTATION:
    """新实现占位符"""
    def execute(self, input_data: Any) -> Any:
        class Output:
            result = {"data": "new result"}
        return Output()


# ========== Fixtures ==========

@pytest.fixture
def test_data() -> List[Dict[str, Any]]:
    """
    准备测试数据集
    
    Returns:
        List[Dict]: 测试用例列表，每个包含:
            - name: 测试用例名称
            - input: 输入数据
            - expected_fields: 期望输出包含的字段
    """
    # TODO: 根据实际需求准备测试数据
    return [
        {
            "name": "简单测试",
            "input": {"file_path": "test1.pdf"},
            "expected_fields": ["data", "confidence"]
        },
        {
            "name": "复杂测试",
            "input": {"file_path": "test2.pdf", "options": {"extract_tables": True}},
            "expected_fields": ["data", "tables", "confidence"]
        }
    ]


@pytest.fixture
def old_impl():
    """创建旧实现实例"""
    return OLD_IMPLEMENTATION()


@pytest.fixture
def new_impl():
    """创建新实现实例"""
    return NEW_IMPLEMENTATION()


# ========== 辅助函数 ==========

def normalize_output(output: Any) -> Dict[str, Any]:
    """
    标准化输出格式，便于对比
    
    不同实现可能返回不同类型，需要转换为统一格式
    
    Args:
        output: 原始输出（dict、Pydantic 模型等）
    
    Returns:
        Dict: 标准化后的字典
    """
    # 如果是 Pydantic 模型
    if hasattr(output, 'model_dump'):
        return output.model_dump()
    
    # 如果是字典
    if isinstance(output, dict):
        return output
    
    # 如果是对象，尝试提取属性
    if hasattr(output, '__dict__'):
        return output.__dict__
    
    # 其他情况
    return {"raw_output": output}


def compare_results(
    old_result: Dict[str, Any],
    new_result: Dict[str, Any],
    tolerance: float = 0.01,
    ignore_fields: List[str] = None
) -> Tuple[bool, List[str]]:
    """
    对比两个结果的一致性
    
    Args:
        old_result: 旧实现结果
        new_result: 新实现结果
        tolerance: 数值容差（浮点数比较）
        ignore_fields: 忽略的字段列表
    
    Returns:
        Tuple[bool, List[str]]: (是否一致, 差异列表)
    """
    ignore_fields = ignore_fields or []
    differences = []
    
    # 检查字段是否一致
    old_keys = set(old_result.keys()) - set(ignore_fields)
    new_keys = set(new_result.keys()) - set(ignore_fields)
    
    if old_keys != new_keys:
        missing_in_new = old_keys - new_keys
        extra_in_new = new_keys - old_keys
        
        if missing_in_new:
            differences.append(f"新实现缺少字段: {missing_in_new}")
        if extra_in_new:
            differences.append(f"新实现多余字段: {extra_in_new}")
    
    # 对比相同字段的值
    for key in old_keys & new_keys:
        old_val = old_result[key]
        new_val = new_result[key]
        
        # 浮点数比较
        if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
            if abs(old_val - new_val) > tolerance:
                differences.append(f"字段 '{key}' 值不同: {old_val} vs {new_val}")
        
        # 字符串比较
        elif isinstance(old_val, str) and isinstance(new_val, str):
            if old_val.strip() != new_val.strip():
                differences.append(f"字段 '{key}' 值不同")
        
        # 列表比较
        elif isinstance(old_val, list) and isinstance(new_val, list):
            if len(old_val) != len(new_val):
                differences.append(f"字段 '{key}' 长度不同: {len(old_val)} vs {len(new_val)}")
        
        # 字典递归比较
        elif isinstance(old_val, dict) and isinstance(new_val, dict):
            is_same, sub_diffs = compare_results(old_val, new_val, tolerance, ignore_fields)
            if not is_same:
                differences.extend([f"{key}.{diff}" for diff in sub_diffs])
        
        # 其他类型直接比较
        else:
            if old_val != new_val:
                differences.append(f"字段 '{key}' 值不同: {type(old_val)} vs {type(new_val)}")
    
    return len(differences) == 0, differences


# ========== 对比测试 ==========

class TestComparison:
    """新旧实现对比测试"""
    
    def test_output_structure_consistency(self, old_impl, new_impl, test_data):
        """测试输出结构一致性"""
        for case in test_data:
            # TODO: 根据实际接口调整调用方式
            # old_output = old_impl.extract(case["input"]["file_path"])
            # new_output = new_impl.execute(...)
            
            # 示例（需要修改）
            old_output = old_impl.extract(case["input"].get("file_path", ""))
            new_output = new_impl.execute(case["input"])
            
            # 标准化输出
            old_normalized = normalize_output(old_output)
            new_normalized = normalize_output(new_output)
            
            # 验证期望字段存在
            for field in case["expected_fields"]:
                assert field in old_normalized or field in new_normalized, \
                    f"测试 '{case['name']}' 缺少字段: {field}"
    
    def test_output_value_consistency(self, old_impl, new_impl, test_data):
        """测试输出值一致性"""
        for case in test_data:
            # TODO: 根据实际接口调整
            old_output = old_impl.extract(case["input"].get("file_path", ""))
            new_output = new_impl.execute(case["input"])
            
            old_normalized = normalize_output(old_output)
            new_normalized = normalize_output(new_output)
            
            # 对比结果（可以忽略某些字段，如 timestamp）
            is_consistent, differences = compare_results(
                old_normalized,
                new_normalized,
                tolerance=0.01,
                ignore_fields=["timestamp", "processing_time", "metadata"]
            )
            
            assert is_consistent, \
                f"测试 '{case['name']}' 结果不一致:\n" + "\n".join(differences)
    
    def test_edge_cases_consistency(self, old_impl, new_impl):
        """测试边界条件一致性"""
        edge_cases = [
            {"name": "空输入", "input": {}},
            {"name": "空字符串", "input": {"file_path": ""}},
            {"name": "不存在的文件", "input": {"file_path": "nonexistent.pdf"}},
        ]
        
        for case in edge_cases:
            try:
                old_output = old_impl.extract(case["input"].get("file_path", ""))
                old_success = True
            except Exception as old_error:
                old_output = None
                old_success = False
            
            try:
                new_output = new_impl.execute(case["input"])
                new_success = True
            except Exception as new_error:
                new_output = None
                new_success = False
            
            # 两者应该同样成功或同样失败
            assert old_success == new_success, \
                f"边界测试 '{case['name']}' 行为不一致: " \
                f"旧实现{'成功' if old_success else '失败'}, " \
                f"新实现{'成功' if new_success else '失败'}"
    
    @pytest.mark.benchmark
    def test_performance_comparison(self, old_impl, new_impl, benchmark):
        """测试性能对比（可选）"""
        test_input = {"file_path": "benchmark_test.pdf"}
        
        # 测试旧实现性能
        old_time = benchmark.pedantic(
            lambda: old_impl.extract(test_input.get("file_path", "")),
            rounds=10,
            iterations=1
        )
        
        # 测试新实现性能
        new_time = benchmark.pedantic(
            lambda: new_impl.execute(test_input),
            rounds=10,
            iterations=1
        )
        
        # 新实现不应该明显慢于旧实现（容忍20%性能下降）
        # assert new_time.mean <= old_time.mean * 1.2, \
        #     f"新实现性能下降过多: {new_time.mean:.4f}s vs {old_time.mean:.4f}s"


# ========== 批量对比测试 ==========

class TestBatchComparison:
    """批量数据对比测试"""
    
    def test_batch_consistency(self, old_impl, new_impl):
        """测试批量处理一致性"""
        # TODO: 准备真实的测试文件
        test_files = [
            "test1.pdf",
            "test2.pdf",
            "test3.pdf"
        ]
        
        results = []
        
        for file_path in test_files:
            try:
                old_output = old_impl.extract(file_path)
                new_output = new_impl.execute({"file_path": file_path})
                
                old_normalized = normalize_output(old_output)
                new_normalized = normalize_output(new_output)
                
                is_consistent, differences = compare_results(
                    old_normalized,
                    new_normalized,
                    ignore_fields=["timestamp", "processing_time"]
                )
                
                results.append({
                    "file": file_path,
                    "consistent": is_consistent,
                    "differences": differences
                })
            except Exception as e:
                results.append({
                    "file": file_path,
                    "consistent": False,
                    "differences": [f"Error: {str(e)}"]
                })
        
        # 统计一致性
        total = len(results)
        consistent_count = sum(1 for r in results if r["consistent"])
        consistency_rate = consistent_count / total if total > 0 else 0
        
        # 期望至少 95% 一致性
        assert consistency_rate >= 0.95, \
            f"一致性率过低: {consistency_rate:.2%} ({consistent_count}/{total})\n" \
            f"不一致的测试:\n" + \
            "\n".join([f"  - {r['file']}: {r['differences']}" 
                      for r in results if not r["consistent"]])


# ========== 生成对比报告 ==========

def generate_comparison_report(old_impl, new_impl, test_data: List[Dict]) -> str:
    """
    生成详细的对比报告
    
    Args:
        old_impl: 旧实现实例
        new_impl: 新实现实例
        test_data: 测试数据集
    
    Returns:
        str: Markdown 格式的对比报告
    """
    report = ["# 新旧实现对比报告\n"]
    report.append(f"**测试时间**: {pytest.__version__}\n")
    report.append(f"**测试用例数**: {len(test_data)}\n\n")
    
    report.append("## 测试结果\n\n")
    report.append("| 测试用例 | 一致性 | 差异 |\n")
    report.append("|---------|--------|------|\n")
    
    for case in test_data:
        try:
            old_output = old_impl.extract(case["input"].get("file_path", ""))
            new_output = new_impl.execute(case["input"])
            
            old_normalized = normalize_output(old_output)
            new_normalized = normalize_output(new_output)
            
            is_consistent, differences = compare_results(old_normalized, new_normalized)
            
            status = "✅" if is_consistent else "❌"
            diff_text = "无" if is_consistent else "<br>".join(differences[:3])
            
            report.append(f"| {case['name']} | {status} | {diff_text} |\n")
        except Exception as e:
            report.append(f"| {case['name']} | ❌ | Error: {str(e)} |\n")
    
    return "".join(report)


# ========== 运行测试 ==========

if __name__ == "__main__":
    """
    直接运行对比测试
    
    命令:
        python -m pytest backend/tests/test_skills/_comparison_test_template.py -v
        python -m pytest backend/tests/test_skills/_comparison_test_template.py -v --tb=short
    """
    pytest.main([__file__, "-v", "--tb=short"])
