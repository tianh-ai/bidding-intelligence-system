# 文件上传功能 - 端到端测试指南

## 测试目标
验证前端文件上传功能的完整流程，从浏览器UI操作到后台处理，再到文件列表显示。

## 测试环境
- **前端**: http://localhost:13000
- **后端API**: http://localhost:18888
- **登录凭证**: 
  - 用户名: `admin`
  - 密码: `admin123`

## 完整测试流程

### 第一步：访问系统并登录

1. 打开浏览器，访问 http://localhost:13000
2. 应看到登录页面
3. 输入凭证：
   - 用户名: `admin`
   - 密码: `admin123`
4. 点击"登录"按钮
5. **验证点**：
   - ✅ 成功跳转到仪表板/主页
   - ✅ Header右上角显示"管理员"标签
   - ✅ 侧边栏显示完整菜单

### 第二步：进入文件上传页面

1. 点击左侧菜单中的"文件上传"（或"File Upload"）
2. **验证点**：
   - ✅ 页面标题显示"文件上传"
   - ✅ 看到上传区域（拖拽或点击上传）
   - ✅ 看到已上传文件列表（可能为空）
   - ✅ 看到数据库统计信息

### 第三步：准备测试文件

由于系统仅支持 PDF, Word, Excel 格式，您需要：

**选项A：使用现有文件**
- 从您的电脑中找一个 `.pdf`, `.docx`, 或 `.xlsx` 文件

**选项B：创建测试PDF（MacOS）**
```bash
# 使用Pages或Word创建一个简单文档
# 内容示例：
"""
测试招标文件
项目编号：TEST-2025-001
日期：2025年12月7日

这是一个用于测试文件上传功能的文档。
"""
# 然后导出为PDF格式
```

**选项C：使用Word文档**
- 创建一个 `.docx` 文件，包含简单文本即可

### 第四步：上传文件

1. 在上传区域：
   - **方式A**: 点击"点击或拖拽文件到此区域"
   - **方式B**: 直接拖拽文件到上传区域
2. 选择您准备的测试文件
3. **验证点**：
   - ✅ 文件出现在待上传列表中
   - ✅ 显示文件名、大小等信息
4. 点击"开始上传"按钮
5. **验证点**：
   - ✅ 看到上传进度条
   - ✅ 显示"成功上传 X 个文件"的消息
   - ✅ 上传人自动填充为当前登录用户（admin）

### 第五步：验证文件处理

**预期行为**：
1. 文件立即上传到临时目录（`temp/`）
2. 后台任务自动启动：
   - 状态变化：`uploaded` → `parsing` → `parsed` → `archiving` → `archived` → `indexed`
3. 文件最终归档到：`archive/{year}/{month}/{category}/`
4. 临时文件被删除

**浏览器验证**：
1. 等待 5-10 秒（后台处理时间）
2. 刷新页面或查看文件列表
3. **验证点**：
   - ✅ 文件出现在"已上传文件"列表中
   - ✅ 显示上传人为 "admin"（或您的用户名）
   - ✅ 显示文件大小
   - ✅ 显示上传时间
   - ✅ 有"下载"和"删除"按钮

### 第六步：后台日志验证（可选）

打开终端，查看后台处理日志：

```bash
# 查看后台处理日志
docker logs bidding_backend --tail 50 | grep -E "(🔄|📝|🏷️|📦|✅)"

# 预期看到：
# 🔄 开始解析: your_file_name.pdf
# 📝 解析完成: X 个章节
# 🏷️ 分类: tender/proposal/other, 语义名: XXX
# 📦 归档到: /app/uploads/archive/2025/12/...
# ✅ 文件处理完成: original_name → semantic_name

# 查看归档目录结构
docker exec bidding_backend find /app/uploads/archive -type f

# 预期看到按年/月/类别组织的文件：
# /app/uploads/archive/2025/12/tender/语义化文件名.pdf
# /app/uploads/archive/2025/12/proposal/...
```

### 第七步：测试文件操作

1. **下载测试**：
   - 点击文件列表中的"下载"按钮
   - **验证点**：
     - ✅ 文件开始下载
     - ✅ 下载的文件可以正常打开

2. **删除测试**：
   - 点击文件列表中的"删除"按钮
   - 确认删除提示
   - **验证点**：
     - ✅ 显示"文件删除成功"消息
     - ✅ 文件从列表中消失

### 第八步：测试重复文件处理

1. 再次上传**相同的文件**（同一个PDF/Word文档）
2. **预期行为**（当前默认策略：`skip`）：
   - ✅ 显示警告消息："文件已存在，已跳过"
   - ✅ 文件不会被重复上传
   - ✅ 列表中只有一份文件

**未来功能**（当前未实现UI）：
- 弹出对话框询问：覆盖/更新/跳过
- 可选择不同的处理策略

### 第九步：测试无效文件格式

1. 尝试上传不支持的文件格式（如 `.txt`, `.jpg`, `.zip`）
2. **验证点**：
   - ✅ 显示错误消息："不支持的文件格式"
   - ✅ 文件不会被上传到服务器

## 已知限制

1. **文件格式限制**：
   - ✅ 支持：PDF (.pdf), Word (.docx, .doc), Excel (.xlsx, .xls)
   - ❌ 不支持：TXT (.txt), 图片, ZIP等其他格式

2. **TXT文件特殊情况**：
   - TXT可以上传到临时目录
   - 但解析引擎不支持，会标记为 `parse_failed`
   - 不影响上传功能本身

3. **重复文件UI**：
   - 当前只有后端策略（skip/overwrite/update）
   - 前端尚未实现重复文件处理对话框
   - 默认行为：跳过重复文件

## 测试数据库状态（高级）

```bash
# 连接数据库查看上传记录
docker exec bidding_postgres psql -U postgres -d bidding_db -c "
SELECT 
  filename, 
  uploader, 
  status, 
  category, 
  semantic_filename,
  uploaded_at::date,
  archived_at::date
FROM uploaded_files 
ORDER BY created_at DESC 
LIMIT 5;
"

# 预期输出示例：
#     filename     | uploader | status  | category |   semantic_filename    | uploaded_at | archived_at
# -----------------+----------+---------+----------+------------------------+-------------+-------------
#  test_doc.pdf    | admin    | indexed | tender   | 2025-12-07_XXX项目.pdf | 2025-12-07  | 2025-12-07
```

## 成功标准

所有以下验证点通过即为成功：

- [x] 用户可以成功登录系统
- [x] 文件上传页面正常加载
- [x] 可以选择并上传支持格式的文件
- [x] 上传后显示成功消息
- [x] 文件出现在已上传列表中
- [x] 显示正确的上传人（当前登录用户）
- [x] 可以下载已上传的文件
- [x] 可以删除已上传的文件
- [x] 重复文件被正确处理（跳过或警告）
- [x] 不支持的格式显示错误消息
- [x] 后台日志显示完整处理流程
- [x] 文件被正确归档到对应目录

## 故障排查

### 问题1：上传后文件列表为空
**原因**：可能后台处理失败
**排查**：
```bash
docker logs bidding_backend --tail 50 | grep -E "(ERROR|❌)"
```

### 问题2：显示"无法获取当前用户信息"
**原因**：未登录或登录状态丢失
**解决**：
1. 按F12打开DevTools
2. Application → Local Storage
3. 检查是否有 `auth-storage` 键
4. 重新登录

### 问题3：上传按钮无响应
**原因**：前端代码未正确加载
**解决**：
```bash
# 重启前端容器
docker restart bidding_frontend
# 等待3秒后刷新浏览器
```

### 问题4：后台处理卡在某个状态
**原因**：解析引擎错误或数据库事务问题
**排查**：
```bash
# 查看详细错误日志
docker logs bidding_backend --tail 100

# 检查文件状态
docker exec bidding_postgres psql -U postgres -d bidding_db -c "
SELECT filename, status, error_log 
FROM uploaded_files 
WHERE status IN ('parse_failed', 'archive_failed')
ORDER BY created_at DESC LIMIT 5;
"
```

## API验证（备用测试方法）

如果浏览器测试失败，可以用curl验证API：

```bash
# 1. 登录获取token（如果需要）
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 上传文件
curl -X POST http://localhost:8000/api/files/upload \
  -F "files=@/path/to/your/file.pdf" \
  -F "uploader=admin" \
  -F "duplicate_action=skip"

# 3. 查看文件列表
curl "http://localhost:8000/api/files?limit=10"
```

## 总结

这是一个**完整的端到端测试流程**，涵盖了从浏览器UI操作到后台处理的所有环节。

**核心验证点**：
1. ✅ 前端上传UI可用
2. ✅ uploader参数正确传递
3. ✅ 后台自动解析和归档
4. ✅ 文件列表正确显示
5. ✅ 用户体验流畅（无需手动刷新）

**下一步优化**：
- [ ] 添加实时状态更新（WebSocket或轮询）
- [ ] 实现重复文件处理对话框
- [ ] 显示文件处理进度条
- [ ] 添加文件预览功能
