# 📚 文档索引 - 模块化架构体系

> **目的**: 快速导航所有架构相关文档  
> **更新日期**: 2025-12-16

---

## 🗂️ 核心文档（骨架）

### 1. 通用规则和原则

| 文档 | 描述 | 优先级 | 状态 |
|------|------|-------|------|
| [DOCKER_PRINCIPLES.md](./DOCKER_PRINCIPLES.md) | Docker 使用原则（最优先） | 🔴 必读 | ✅ 完成 |
| [PORT_CONSISTENCY.md](./PORT_CONSISTENCY.md) | 端口一致性原则（强制） | 🔴 必读 | ✅ 完成 |
| [CODE_PROTECTION.md](./CODE_PROTECTION.md) | 代码保护规范 | 🔴 必读 | ✅ 完成 |
| [FRONTEND_BEHAVIOR.md](./FRONTEND_BEHAVIOR.md) | 前端行为规范 | 🟡 重要 | ✅ 完成 |

---

### 2. 架构设计（本次梳理）

| 文档 | 描述 | 优先级 | 状态 |
|------|------|-------|------|
| [**MODULAR_ARCHITECTURE.md**](./MODULAR_ARCHITECTURE.md) | 🏗️ **模块化架构总览** | 🔴 核心 | ✅ 完成 |
| [**MODULE_INVENTORY.md**](./MODULE_INVENTORY.md) | 📦 **功能模块清单** | 🔴 核心 | ✅ 完成 |
| [**MIGRATION_PLAN.md**](./MIGRATION_PLAN.md) | 🚀 **迁移实施计划** | 🔴 核心 | ✅ 完成 |
| [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md) | 系统架构总览（旧版） | 🟢 参考 | ✅ 已有 |

---

### 3. 技术指南

| 文档 | 描述 | 优先级 | 状态 |
|------|------|-------|------|
| [README.md](./README.md) | 项目总览和快速开始 | 🔴 必读 | ✅ 完成 |
| [backend/README.md](./backend/README.md) | 后端架构说明 | 🟡 重要 | ✅ 完成 |
| [CONFIGURATION_GUIDE.md](./CONFIGURATION_GUIDE.md) | 配置管理指南 | 🟡 重要 | ✅ 完成 |
| [DOCKER_GUIDE.md](./DOCKER_GUIDE.md) | Docker 使用指南 | 🟡 重要 | ✅ 完成 |

---

### 4. MCP 相关文档

| 文档 | 描述 | 优先级 | 状态 |
|------|------|-------|------|
| [mcp-servers/README.md](./mcp-servers/README.md) | MCP 服务器总览 | 🔴 核心 | ✅ 完成 |
| [mcp-servers/document-parser/README.md](./mcp-servers/document-parser/README.md) | 文档解析 MCP | 🟡 重要 | ✅ 完成 |
| [mcp-servers/knowledge-base/README.md](./mcp-servers/knowledge-base/README.md) | 知识库 MCP | 🟡 重要 | ✅ 完成 |
| [MCP_PARSER_SETUP.md](./MCP_PARSER_SETUP.md) | MCP 解析器设置 | 🟢 参考 | ✅ 完成 |

---

## 📖 阅读顺序建议

### 🎯 新手入门（第一天）

1. **README.md** - 了解项目概况
2. **DOCKER_PRINCIPLES.md** - 掌握 Docker 规则（最重要！）
3. **PORT_CONSISTENCY.md** - 记住端口 18888
4. **CODE_PROTECTION.md** - 学习代码保护

---

### 🏗️ 架构理解（第二天）

1. **MODULAR_ARCHITECTURE.md** - 理解新架构设计
   - MCP vs Skill 的区别
   - 目录结构规范
   - 接口规范

2. **MODULE_INVENTORY.md** - 了解现有模块
   - 哪些已实现
   - 哪些待开发
   - 优先级排序

3. **MIGRATION_PLAN.md** - 掌握迁移计划
   - 6周时间线
   - 每个阶段的任务
   - 验收标准

---

### 🛠️ 开发实践（第三天起）

1. **backend/README.md** - 后端开发规范
2. **mcp-servers/README.md** - MCP 开发指南
3. **CONFIGURATION_GUIDE.md** - 配置管理

---

## 🔍 快速查找

### 我想知道...

#### "如何创建新的 MCP 服务器？"
👉 [MODULAR_ARCHITECTURE.md - 7.1 创建新 MCP 服务器](./MODULAR_ARCHITECTURE.md#71-创建新-mcp-服务器)

#### "如何创建新的 Skill？"
👉 [MODULAR_ARCHITECTURE.md - 7.2 创建新 Skill](./MODULAR_ARCHITECTURE.md#72-创建新-skill)

#### "哪些功能适合做成 MCP？"
👉 [MODULAR_ARCHITECTURE.md - 2. 模块分类策略](./MODULAR_ARCHITECTURE.md#2-模块分类策略)

#### "如何迁移现有代码？"
👉 [MIGRATION_PLAN.md - 完整实施计划](./MIGRATION_PLAN.md)

#### "端口配置怎么检查？"
👉 运行 `./check_ports.sh` + 阅读 [PORT_CONSISTENCY.md](./PORT_CONSISTENCY.md)

#### "Docker 怎么用？"
👉 [DOCKER_PRINCIPLES.md](./DOCKER_PRINCIPLES.md)

#### "哪些文件不能改？"
👉 [CODE_PROTECTION.md](./CODE_PROTECTION.md)

---

## 📊 文档状态

### 已完成文档 ✅
- MODULAR_ARCHITECTURE.md
- MODULE_INVENTORY.md
- MIGRATION_PLAN.md
- DOCUMENTATION_INDEX.md（本文件）

### 待创建文档 📝
- docs/API_STANDARDS.md
- docs/TESTING_GUIDE.md
- backend/skills/README.md

---

**维护者**: Copilot + 开发团队  
**最后更新**: 2025-12-16
