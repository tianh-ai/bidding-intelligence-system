# 代码保护规范

**创建时间**: 2025-12-14  
**更新时间**: 2025-12-14  
**状态**: 强制执行  
**优先级**: 🔴 最高

---

## 🎯 核心原则

> **不要修改已经验证工作正常的代码！**

这个原则看似简单，但Copilot经常违反，导致：
- ✅ 工作的功能被破坏
- 🐛 引入新的bug
- 🔄 需要回滚修改
- ⏰ 浪费时间重新测试

---

## 🔒 受保护的文件（禁止随意修改）

### 前端核心文件

以下文件**已经过验证并正常工作**，除非有明确的bug报告，否则**禁止修改**：

#### 前端关键文件
```
frontend/src/pages/FileUpload.tsx
  - ✅ 文件上传逻辑 (handleUpload函数)
  - ✅ 初始化行为 (useEffect - 不自动加载历史数据)
  - ✅ 自动刷新机制 (useEffect - autoRefresh)
  - ✅ 重复文件处理
  - ⚠️  可安全修改区域: 样式、UI组件、console.log

frontend/src/pages/FileSummary.tsx
  - ✅ 文件摘要显示
  - ✅ 学习功能集成
  - ⚠️  可安全修改: 新增Tab、优化UI

frontend/src/services/api.ts
  - ✅ API客户端配置
  - ✅ 所有API函数定义
  - ⚠️  可安全修改: 新增API函数（但不修改现有）
```

#### 后端关键文件
```
backend/routers/files.py
  - ✅ 文件上传逻辑
  - ✅ 重复文件检测
  - ✅ 异步任务触发
  - ⚠️  可安全修改: 新增路由、优化错误处理

backend/agents/preprocessor.py
  - ✅ PDF解析逻辑
  - ✅ 表格提取
  - ⚠️  慎重修改: 任何改动需要充分测试

backend/engines/smart_router.py
  - ✅ 85/10/5路由策略
  - ⚠️  禁止修改: 除非有单元测试覆盖
```

### 2. 修改前检查清单

在修改任何文件前，必须：

- [ ] 阅读 `FRONTEND_BEHAVIOR.md` 确认预期行为
- [ ] 检查文件是否在上述"禁止修改"列表中
- [ ] 如果必须修改，先创建备份
- [ ] 运行相关测试验证当前功能正常
- [ ] 修改后立即测试，确保功能不被破坏

### 3. 安全修改指南

#### ✅ 允许的操作

1. **新增功能**（不影响现有代码）
   ```typescript
   // ✅ 添加新的API函数
   export const newAPI = {
     newMethod: () => axiosInstance.get('/new/endpoint')
   }
   
   // ✅ 添加新的state
   const [newFeature, setNewFeature] = useState()
   
   // ✅ 添加新的Tab
   <Tabs.TabPane key="new-tab" tab="新功能">
   ```

2. **优化UI/样式**
   ```typescript
   // ✅ 修改className
   <div className="updated-style">
   
   // ✅ 调整布局
   <Space direction="vertical" size="large">
   ```

3. **添加日志和调试**
   ```typescript
   // ✅ 添加console.log
   console.log('调试信息:', data)
   
   // ✅ 添加错误处理
   try {
     // 现有代码
   } catch (error) {
     console.error('新的错误处理:', error)
   }
   ```

#### ❌ 禁止的操作

1. **修改已验证的业务逻辑**
   ```typescript
   // ❌ 不要修改上传逻辑
   const handleUpload = async () => {
     // 这里的代码已经过验证，不要改！
   }
   
   // ❌ 不要修改初始化逻辑
   useEffect(() => {
     // 不自动加载是正确行为，不要取消注释！
     // loadUploadedFiles()  // ❌ 禁止取消注释
   }, [])
   ```

2. **删除现有功能**
   ```typescript
   // ❌ 不要删除现有函数
   // const loadUploadedFiles = async () => { ... }
   
   // ❌ 不要删除现有state
   // const [uploadedFilesList, setUploadedFilesList] = useState([])
   ```

3. **重构未经测试的代码**
   ```typescript
   // ❌ 不要重构没有单元测试的函数
   // const oldFunction = () => { ... }  // 有100+行复杂逻辑
   // 改成
   // const newFunction = () => { ... }  // 全新实现
   ```

### 4. 代码审查检查点

#### 前端代码审查
- [ ] 是否修改了 `handleUpload` 函数？
- [ ] 是否修改了 `useEffect` 初始化逻辑？
- [ ] 是否取消了注释的自动加载函数？
- [ ] 是否修改了 API调用格式？
- [ ] 新增的代码是否与现有代码冲突？

#### 后端代码审查
- [ ] 是否修改了文件上传路由？
- [ ] 是否修改了重复文件检测逻辑？
- [ ] 是否修改了异步任务触发机制？
- [ ] 新增的代码是否影响现有API？
- [ ] 是否更新了相关配置？

### 5. 测试验证流程

#### 前端测试
```bash
# 1. 编译检查
cd frontend && npm run build

# 2. 启动开发服务器
npm run dev

# 3. 浏览器验证
# - 打开 http://localhost:5173
# - 测试文件上传
# - 检查控制台是否有错误
# - 验证知识库显示
```

#### 后端测试
```bash
# 1. 运行验证脚本
python verify_knowledge_display.py

# 2. 运行单元测试（如果有）
pytest tests/ -v

# 3. 手动API测试
curl -X POST http://localhost:8000/api/knowledge/entries/list \
  -H 'Content-Type: application/json' \
  -d '{"limit": 5}'
```

### 6. 版本控制策略

#### 提交前检查
```bash
# 1. 查看修改
git diff

# 2. 确认修改的文件
git status

# 3. 分批提交（不要一次提交所有修改）
git add frontend/src/components/NewFeature.tsx
git commit -m "feat: 添加新功能（不影响现有代码）"

# 4. 如果修改了关键文件，单独提交
git add frontend/src/pages/FileUpload.tsx
git commit -m "fix: 修复FileUpload的XXX问题（已测试）"
```

#### 回滚策略
```bash
# 如果发现修改破坏了功能，立即回滚

# 1. 回滚单个文件
git checkout HEAD -- frontend/src/pages/FileUpload.tsx

# 2. 回滚到上一次提交
git reset --hard HEAD^

# 3. 回滚到特定提交
git reset --hard <commit-hash>
```

### 7. 知识库显示问题诊断

如果知识库不显示内容，按以下顺序检查：

```bash
# 1. 运行诊断脚本
python verify_knowledge_display.py

# 2. 检查服务状态
# - 后端: curl http://localhost:8000/health
# - 前端: 打开浏览器开发者工具

# 3. 检查数据库
psql -h localhost -p 5433 -U postgres -d bidding_db
SELECT COUNT(*) FROM knowledge_entries;

# 4. 检查前端代码是否被修改
git diff frontend/src/pages/FileUpload.tsx

# 5. 如果代码被修改且不应该，立即回滚
git checkout HEAD -- frontend/src/pages/FileUpload.tsx
```

### 8. 常见错误预防

#### 错误1: 修改工作代码导致功能失效
```typescript
// ❌ 错误示例
// 原始代码（工作正常）
const loadKnowledgeEntriesForFiles = async (fileIds: string[]) => {
  // ... 正确实现
}

// 被修改成（功能失效）
const loadKnowledgeEntriesForFiles = async (fileIds: string[]) => {
  // ... 新的实现（未测试）
}

// ✅ 正确做法
// 如果需要修改，先创建新函数
const loadKnowledgeEntriesForFilesV2 = async (fileIds: string[]) => {
  // ... 新实现
}
// 测试通过后再替换
```

#### 错误2: 取消注释导致行为改变
```typescript
// ❌ 错误示例
useEffect(() => {
  loadUploadedFiles()  // 取消了注释
  // ^^^ 这会导致页面自动加载历史文件（违反规范）
}, [])

// ✅ 正确做法
// 不要取消注释！这是设计行为
useEffect(() => {
  // loadUploadedFiles()  // 保持注释
}, [])
```

#### 错误3: 重复修改导致代码混乱
```typescript
// ❌ 错误示例
// 同一个文件被多次修改，导致代码重复
const loadKnowledgeEntriesForFiles = async (fileIds: string[]) => {
  // 第一次修改
}
const loadKnowledgeEntriesForFiles = async (fileIds: string[]) => {
  // 第二次修改（重复定义）
}

// ✅ 正确做法
// 一次到位，修改前充分思考
```

## 📋 快速检查命令

```bash
# 检查文件是否被修改
git diff --name-only

# 检查特定文件的修改
git diff frontend/src/pages/FileUpload.tsx

# 恢复文件到未修改状态
git checkout -- frontend/src/pages/FileUpload.tsx

# 运行完整诊断
python verify_knowledge_display.py
```

## 🎯 总结

**核心原则**: 
- 如果代码已经工作，不要修改它
- 如果必须修改，先测试、再提交
- 出现问题立即回滚，不要尝试修复未知问题
- 新功能独立开发，不影响现有功能

**记住**: 
- ⚠️  **不予许对已经正确的代码进行改动**
- ✅ **每次修改前运行 `verify_knowledge_display.py`**
- 🔄 **修改后立即验证功能是否正常**
