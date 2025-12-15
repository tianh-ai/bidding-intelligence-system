# 未解决问题归档：DOCX 目录解析不一致（缺失“第X部分/第二部分”）

日期：2025-12-14

## 问题摘要
两份结构几乎相同的 DOCX（同为“商务文件/投标函”段落）在系统内生成的“文档目录索引”不一致：
- 文件 A 会生成 L1 章节：`第二部分 / 商务文件`，其下再有 `一~六`。
- 文件 B 只生成 L2 `一~六`，缺失 L1 `第二部分 / 商务文件`。

这会导致前端“文档目录索引”出现不一致/重复展示（截图中可见 `第二部分一、投标函（招标）` 与 `第二部分 商务文件` 等）。

## 涉及文件（file_id）
- A：`56a4616d-1cd9-4a5e-ba50-0f6b1ca74dfe`
  - semanticName 含：`ab7b3f`
- B：`3de3a2d5-49c5-49ab-9067-9b5b528e606f`
  - semanticName 含：`f79003`

## 现象与证据（接口返回）
### 1) DB 章节输出（当前仍不一致）
- A：`GET http://localhost:18888/api/files/56a4616d-1cd9-4a5e-ba50-0f6b1ca74dfe/chapters`
  - `total=7`
  - 首条章节：`chapter_number=第二部分`、`chapter_title=商务文件`、`chapter_level=1`
- B：`GET http://localhost:18888/api/files/3de3a2d5-49c5-49ab-9067-9b5b528e606f/chapters`
  - `total=6`
  - 首条章节：`chapter_number=一`、`chapter_title=投标函`、`chapter_level=2`

### 2) 抽取文本头部（证据：B 缺失“第二部分”）
- A：`GET http://localhost:18888/api/diagnostics/extract-preview/56a4616d-1cd9-4a5e-ba50-0f6b1ca74dfe?max_lines=25`
  - head_lines 中包含：`第二部分   商务文件`
- B：`GET http://localhost:18888/api/diagnostics/extract-preview/3de3a2d5-49c5-49ab-9067-9b5b528e606f?max_lines=25`
  - head_lines 以 `商务文件` 开头
  - **未出现** `第二部分`（或 `第X部分`）

结论：目录分叉根因在“DOCX 文本抽取阶段”，而不是章节识别器本身。

## 已尝试的修复（当前未完全生效）
### 1) 增强 DOCX 抽取
文件：`backend/engines/parse_engine.py`
- `_parse_docx()` 改为按文档顺序抽取 **段落+表格**
- 尝试抽取 **页眉/页脚**
- 增加 **OOXML `w:t` 节点兜底**：从 OOXML 文本中探测 `第X部分`，并在首行是 `商务文件` 且缺失 `第X部分` 时补成 `第X部分   商务文件`

### 2) 增加诊断端点（已生效）
文件：
- `backend/routers/diagnostics.py`
- `backend/main.py`（已 include router）

端点：
- `/api/diagnostics/extract-preview/{file_id}`
- `/api/diagnostics/reparse/{file_id}`（GET/POST 都可）

## 当前状态
- 诊断端点可用，能证明 B 的抽取头部仍缺失 `第二部分`。
- 由于 B 的原始抽取文本缺失该标识，章节树自然缺失 L1。

## 待复验步骤（下次继续时优先做）
1. 重启后端（确保容器加载最新代码）：
   - `docker compose restart backend`
2. 复查 B 的抽取头部是否已补回 `第二部分`：
   - `GET /api/diagnostics/extract-preview/{B}?max_lines=10`
3. 对 B 执行重解析并落库：
   - `GET /api/diagnostics/reparse/{B}`
4. 再查章节树是否出现 L1：
   - `GET /api/files/{B}/chapters`

## 下一步排查方向（若仍失败）
如果 B 的 `第二部分` 在 Word 里实际是：
- 图片 / 扫描件（非文本）
- 嵌入对象（OLE）
- 非 w:t 可见文本（极少见）

则需要：
- 进一步从 docx 的 media/ 或关系中定位该标题所在对象
- 或对“标题图片”启用 OCR（仅针对标题区域，避免全量 OCR）

## 备注
本归档仅记录未解决问题与证据，不作为最终修复说明。
