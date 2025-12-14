# 文件显示逻辑关键修复

**修复日期**: 2025-12-14  
**重要性**: 🔴 CRITICAL - 不得随意修改  

## 修复的三个核心问题

### ✅ 问题1: 页面初始化清空历史文件
**状态**: 已验证正确，无需修改

**实现位置**: `frontend/src/pages/FileUpload.tsx` 第83-108行

**关键代码**:
```typescript
useEffect(() => {
  // 1. 清空本地UI状态
  setFileList([])
  setUploadedFilesList([])
  setDocumentIndexes([])
  // ...
  
  // 2. 不自动加载服务器数据
  // loadUploadedFiles()  // ❌ 禁止取消注释
  // loadDocumentIndexes() // ❌ 禁止取消注释
}, []) // 只在组件挂载时执行一次
```

**保护规则**:
- ❌ 禁止在 useEffect 中调用任何 load* 函数
- ❌ 禁止修改依赖数组（必须保持为空数组 `[]`）
- ✅ 只允许在上传成功后加载数据

---

### ✅ 问题2: 重复文件显示逻辑
**状态**: 已完整修复

**需求**:
1. 上传重复文件时，在左侧列表显示并标记"重复文件"
2. 右侧显示重复文件的目录索引和知识库条目
3. 处理完成后重复文件不会消失

**实现位置**: `frontend/src/pages/FileUpload.tsx`

#### 关键状态变量 (第73-85行):
```typescript
const [currentUploadIds, setCurrentUploadIds] = useState<string[]>([])
const [allDisplayFileIds, setAllDisplayFileIds] = useState<string[]>([])
const [duplicateFilesList, setDuplicateFilesList] = useState<any[]>([])
```

**保护规则**:
- ❌ 禁止删除这三个状态变量
- ❌ 禁止在自动刷新时只使用 `currentUploadIds`
- ✅ 必须使用 `allDisplayFileIds` 加载目录和知识库

#### 上传成功处理 (第298-340行):
```typescript
// 1. 收集新上传文件ID
const uploadedIds = result.uploaded.map((f: any) => f.id)
setCurrentUploadIds(uploadedIds)

// 2. 收集重复文件ID和显示信息
const duplicates: any[] = []
result.duplicates.forEach((dup: any) => {
  allFileIds.push(dup.existing_id)
  const duplicateFile = {
    id: dup.existing_id,
    isDuplicate: true,  // ⚠️ 关键标记
    // ...
  }
  duplicates.push(duplicateFile)
})

// 3. 保存所有文件ID
setAllDisplayFileIds(allFileIds)
setDuplicateFilesList(duplicates)
```

**保护规则**:
- ✅ `allFileIds` 必须包含新上传和重复文件的ID
- ✅ 重复文件必须设置 `isDuplicate: true`
- ❌ 禁止只使用 `result.uploaded` 设置文件列表

#### 自动刷新逻辑 (第115-145行):
```typescript
// 合并新上传文件和重复文件
const currentFiles = allFiles.filter((f: any) => currentUploadIds.includes(f.id))
const combinedFiles = [...currentFiles, ...duplicateFilesList]
setUploadedFilesList(combinedFiles)

// 处理完成时使用 allDisplayFileIds
if (!hasProcessing) {
  await loadSpecificDocumentIndexes(allDisplayFileIds)  // ⚠️ 使用全部文件ID
  await loadKnowledgeEntriesForFiles(allDisplayFileIds)
}
```

**保护规则**:
- ✅ 必须合并 `currentFiles` 和 `duplicateFilesList`
- ✅ 必须使用 `allDisplayFileIds` 而非 `currentUploadIds`
- ❌ 禁止只显示 `currentFiles`

#### 重复文件UI标识 (第421-443行):
```typescript
const isDuplicate = (record as any).isDuplicate || false

return (
  <Space>
    <FileTextOutlined />
    <span>{text}</span>
    {isDuplicate && <Tag color="warning">重复文件</Tag>}  // ⚠️ 关键标记
  </Space>
)
```

**保护规则**:
- ✅ 必须检查 `isDuplicate` 字段
- ✅ 重复文件必须显示"重复文件"标签
- ❌ 禁止移除重复文件的特殊处理

---

### ✅ 问题3: 文件名显示统一
**状态**: 已完整修复

**需求**: 所有地方（左侧列表、右侧目录、知识库）显示相同的原始文件名

**实现位置**: `backend/routers/files.py`

#### 文档索引API (第1109-1125行):
```python
# JOIN uploaded_files 获取原始文件名
if fileId:
    files = db.query_all("""
        SELECT f.*, uf.filename as original_filename
        FROM files f
        LEFT JOIN uploaded_files uf ON f.id = uf.id
        WHERE f.id = %s
    """, (fileId,))
else:
    files = db.query_all("""
        SELECT f.*, uf.filename as original_filename
        FROM files f
        LEFT JOIN uploaded_files uf ON f.id = uf.id
        ORDER BY f.created_at DESC
        LIMIT 50
    """)
```

**保护规则**:
- ✅ 必须 JOIN `uploaded_files` 表
- ✅ 必须 SELECT `uf.filename as original_filename`
- ❌ 禁止只从 `files` 表查询

#### 文件名优先级 (第1155-1162行):
```python
# 优先级: uploaded_files.filename > metadata.original_filename > files.filename
display_name = file.get('original_filename') or file['filename']
if not file.get('original_filename') and file.get('metadata'):
    display_name = file['metadata'].get('original_filename', file['filename'])

document_indexes.append({
    'id': file['id'],
    'fileName': display_name,  // ⚠️ 使用原始文件名
    'chapters': chapter_tree
})
```

**保护规则**:
- ✅ 优先使用 `original_filename`（来自 uploaded_files 表）
- ✅ 其次使用 `metadata.original_filename`
- ✅ 最后才使用 `files.filename`（语义化文件名）
- ❌ 禁止直接使用 `file['filename']`

#### 知识库API (第1022-1035行):
```python
entries = db.query("""
    SELECT 
        f.id,
        COALESCE(uf.filename, f.filename) as title,
        COALESCE(uf.filename, f.filename) as "fileName",
        -- ...
    FROM files f
    LEFT JOIN uploaded_files uf ON f.id = uf.id
    LEFT JOIN chapters c ON f.id = c.file_id
    GROUP BY f.id, f.filename, uf.filename, f.doc_type, f.created_at
""")
```

**保护规则**:
- ✅ 必须使用 `COALESCE(uf.filename, f.filename)`
- ✅ GROUP BY 必须包含 `uf.filename`
- ❌ 禁止只使用 `f.filename`

---

## 数据流图

```
上传文件
  ├─ 新文件
  │   ├─ 保存到 currentUploadIds
  │   ├─ 保存到 allDisplayFileIds
  │   └─ 显示在文件列表（状态标签）
  │
  └─ 重复文件
      ├─ 保存到 allDisplayFileIds
      ├─ 保存到 duplicateFilesList
      └─ 显示在文件列表（"重复文件"标签）

自动刷新
  ├─ 更新新文件状态（currentUploadIds）
  ├─ 合并重复文件（duplicateFilesList）
  └─ 显示合并后的列表

处理完成
  ├─ 使用 allDisplayFileIds 加载目录
  ├─ 使用 allDisplayFileIds 加载知识库
  └─ 显示所有文件（新+重复）
```

---

## 测试验证清单

### 场景1: 上传新文件
- [ ] 刷新页面后左右两侧为空
- [ ] 上传2个新文件
- [ ] 左侧显示2个文件，状态为"处理中"
- [ ] 右侧目录显示2个文件的章节
- [ ] 处理完成后状态变为"已完成"
- [ ] 所有地方显示原始文件名

### 场景2: 上传重复文件
- [ ] 上传1个已存在的文件
- [ ] 左侧显示该文件并标记"重复文件"
- [ ] 右侧目录显示该文件的章节
- [ ] 右侧知识库显示该文件的条目
- [ ] 所有地方显示原始文件名

### 场景3: 混合上传
- [ ] 同时上传1个新文件 + 1个重复文件
- [ ] 左侧显示2个文件，重复文件有"重复文件"标签
- [ ] 右侧目录显示2个文件的章节
- [ ] 新文件处理完成后，重复文件仍然显示
- [ ] 所有地方显示原始文件名

---

## 紧急回滚指南

如果修改导致问题，立即恢复以下文件：

### 后端
```bash
cd backend
git checkout HEAD -- routers/files.py
docker-compose restart backend
```

### 前端
```bash
cd frontend/src/pages
git checkout HEAD -- FileUpload.tsx
# HMR会自动应用
```

---

## 相关文档

- `FRONTEND_BEHAVIOR.md` - 前端行为规范
- `backend/routers/files.py` - 文件路由实现
- `frontend/src/pages/FileUpload.tsx` - 文件上传页面

---

**⚠️ 警告**: 
1. 任何修改前必须先阅读本文档
2. 修改后必须通过所有测试验证清单
3. 禁止"优化"或"简化"这些逻辑，除非有严重bug
4. 保持 JOIN uploaded_files 的查询方式，这是获取原始文件名的唯一可靠方法
