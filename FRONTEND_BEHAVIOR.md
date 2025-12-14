# 前端行为规范文档

**创建时间**: 2025-12-14  
**状态**: 已确认 - 不要修改

## ⚠️ 关键行为：页面初始化不自动加载历史数据

### 文件上传页面 (FileUpload.tsx)

**确认的行为**：
- ✅ 每次打开页面时，**不自动显示**服务器上已存在的文件
- ✅ 页面保持空白状态，等待用户手动上传
- ✅ 只有上传成功后，才加载并显示数据

**实现位置**：
```typescript
// frontend/src/pages/FileUpload.tsx
// 初始加载数据 - 每次打开页面重置所有状态（不自动加载已上传文件）
useEffect(() => {
  // 1. 清空本地UI状态
  setFileList([])
  setSelectedDoc(null)
  setProcessingFiles(new Set())
  setAutoRefresh(false)
  setUploadProgress(0)
  setUploading(false)
  setCollapsedDocs(new Set())
  setExpandedKeys({})
  setAllExpanded({})
  
  // 2. 清空数据列表（不显示之前的文件）
  setUploadedFilesList([])
  setKnowledgeEntries([])
  setDocumentIndexes([])
  setDatabaseStats(null)
  
  // 3. 不自动加载服务器数据，等待用户手动上传或刷新
  // loadUploadedFiles()       // ❌ 已注释 - 不要取消注释
  // loadDatabaseStats()       // ❌ 已注释 - 不要取消注释
  // loadKnowledgeEntries()    // ❌ 已注释 - 不要取消注释
  // loadDocumentIndexes()     // ❌ 已注释 - 不要取消注释
}, [])
```

**数据加载时机**：
仅在以下情况加载数据：
1. 用户上传文件成功后 (`handleUpload` 函数内的 `Promise.all([...])`)
2. 用户删除文件后 (`handleDeleteFile` 函数)
3. 自动刷新机制触发时（文件处理中状态）

### 逻辑学习页面 (LogicLearning.tsx)

**确认的行为**：
- ✅ 清除上次会话的临时选择和任务状态
- ✅ 保留逻辑库备份（localStorage持久化数据）
- ✅ 重新加载可用文件列表和逻辑数据库

**实现位置**：
```typescript
// frontend/src/pages/LogicLearning.tsx
useEffect(() => {
  // 清除上次会话的临时状态
  setSelectedFiles([])
  setLearningTask(null)
  setGenerationTask(null)
  setUploadQueue([])
  setUploadProgress(0)
  setSelectedLogic(null)
  setSelectedBucket(null)
  setLogicEditor(initialEditorState)
  setWorkspaceMessages([])
  setHumanFeedback('')
  
  // 加载持久化数据
  loadAvailableFiles()
  loadLogicDatabase()
  loadBackups()
}, [])
```

### 文件总结页面 (FileSummary.tsx)

**确认的行为**：
- ✅ 清空所有输入框和总结内容
- ✅ 重置Tab到默认状态
- ✅ 重新加载文件列表

**实现位置**：
```typescript
// frontend/src/pages/FileSummary.tsx
useEffect(() => {
  // 清除上次会话状态
  setLinkInput('')
  setFileId('')
  setFolderPath('')
  setSummary('')
  setActiveTab('link')
  
  // 加载文件列表
  loadFiles()
}, [])
```

---

## 🚫 禁止的修改

**以下修改被明确禁止，除非用户明确要求：**

1. ❌ 在 `FileUpload.tsx` 的初始化 `useEffect` 中取消注释任何加载函数
2. ❌ 添加自动加载历史文件的逻辑
3. ❌ 修改页面初始状态为"加载中"而不是"空白"
4. ❌ 在组件挂载时调用任何文件列表API

---

## ✅ 允许的修改

**以下修改是允许的：**

1. ✅ 优化上传成功后的数据刷新逻辑
2. ✅ 改进自动刷新机制（文件处理状态监控）
3. ✅ 添加手动"刷新"按钮供用户主动加载数据
4. ✅ 修复任何不影响初始化行为的bug

---

## 📋 验证方法

**如何验证前端行为正确**：

1. 打开浏览器访问 `http://localhost:13000/files`
2. 刷新页面 (Cmd+R 或 Ctrl+R)
3. **预期结果**：
   - 已上传文件列表：空（0个文件）
   - 知识库条目：空
   - 文档索引：空
   - 数据库统计：空或0
4. 上传新文件后，才显示数据

---

## 🔍 相关文件

**主要文件**：
- `frontend/src/pages/FileUpload.tsx` (行 82-105)
- `frontend/src/pages/LogicLearning.tsx` (行 81-95)
- `frontend/src/pages/FileSummary.tsx` (行 16-24)

**不要修改这些文件的初始化逻辑，除非有明确的用户需求变更。**

---

**最后确认时间**: 2025-12-14 12:15 UTC+8  
**确认人**: 用户明确要求 - "不应当显示这两个之前已经上传的文件"
