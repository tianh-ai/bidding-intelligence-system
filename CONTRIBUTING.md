# 贡献指南

感谢您对标书智能系统的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告Bug

如果您发现了bug，请：

1. 检查 [Issues](https://github.com/your-username/bidding-intelligence-system/issues) 是否已有相同问题
2. 如果没有，创建新Issue并包含：
   - 清晰的标题和描述
   - 复现步骤
   - 预期行为和实际行为
   - 系统环境（OS、Python版本等）
   - 错误日志（如有）

### 提交功能请求

1. 在Issues中描述您的想法
2. 说明为什么这个功能有用
3. 提供示例或用例

### 提交代码

1. **Fork仓库**
   ```bash
   git clone https://github.com/your-username/bidding-intelligence-system.git
   cd bidding-intelligence-system
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **开发和测试**
   - 遵循代码规范
   - 添加必要的测试
   - 确保所有测试通过

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

5. **创建Pull Request**
   - 描述您的更改
   - 引用相关的Issue

## 📝 代码规范

### Python代码规范

- 遵循 PEP 8
- 使用类型提示
- 编写文档字符串

示例：
```python
def parse_document(file_path: str, doc_type: str) -> Dict[str, Any]:
    """
    解析文档文件
    
    Args:
        file_path: 文件路径
        doc_type: 文档类型（requirement/similar）
    
    Returns:
        包含解析结果的字典
    
    Raises:
        ValueError: 当文件格式不支持时
    """
    # 实现代码
    pass
```

### 提交信息规范

格式：`<type>(<scope>): <subject>`

类型：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例：
```
feat(parse): add Word document support
fix(database): resolve connection timeout issue
docs(readme): update installation guide
```

## 🧪 测试要求

所有新功能和bug修复都应包含测试：

```bash
# 运行测试
pytest

# 运行指定测试
pytest tests/test_your_feature.py

# 查看覆盖率
pytest --cov=backend tests/
```

## 📋 Pull Request 检查清单

提交PR前，请确认：

- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 没有合并冲突

## ❓ 需要帮助？

- 查看 [README.md](README.md)
- 浏览现有的 [Issues](https://github.com/your-username/bidding-intelligence-system/issues)
- 阅读 [API文档](API_USAGE.md)

感谢您的贡献！
