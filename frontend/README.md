# 投标智能系统 - 前端

基于 Vite + React + TypeScript + Refine + Ant Design 构建的现代化投标文件管理系统前端。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 库**: Ant Design 5 (暗色主题)
- **数据管理**: Refine + Zustand
- **路由**: React Router v6
- **样式**: Tailwind CSS
- **HTTP 客户端**: Axios
- **Markdown 渲染**: React Markdown

## 功能特性

### 核心功能

1. **用户认证与权限**
   - 三级权限系统（管理员、用户、访客）
   - JWT 认证
   - 权限控制

2. **文件上传及存档**
   - 支持多文件/文件夹上传
   - 自动文件分类和匹配
   - 智能存储管理

3. **逻辑学习**
   - 从历史文件学习生成逻辑
   - 从历史文件学习检查逻辑
   - 逻辑库管理（永久逻辑 + 临时逻辑）
   - 投标文件生成
   - 自动检查与迭代优化

4. **文件总结**
   - 招标公告链接总结
   - 文件/文件夹总结
   - 提示词管理（管理员）

5. **标书生成**
   - 智能生成投标文件
   - 人机交互确认
   - 自动评价与修改
   - 迭代优化

6. **大模型管理**
   - 多模型支持（OpenAI、DeepSeek、通义千问等）
   - API Key 管理
   - 模型参数配置
   - 模型测试

7. **AI 助手**
   - 右侧固定对话窗口
   - 多轮对话支持
   - 上下文记忆

### UI/UX 特性

- **Grok 风格设计**
  - 暗色主题
  - 现代化界面
  - 流畅动画

- **VSCode 风格布局**
  - 左侧可折叠导航
  - 中间主工作区
  - 右侧 AI 对话面板
  - 可调整面板宽度

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
# 或
pnpm install
```

### 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
VITE_API_URL=http://localhost:18888
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:13000

### 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── components/      # 可复用组件
│   │   ├── AIChatPanel.tsx       # AI 对话面板
│   │   ├── AppHeader.tsx         # 顶部栏
│   │   └── AppSidebar.tsx        # 侧边栏
│   ├── config/          # 配置文件
│   │   └── constants.ts          # 常量配置
│   ├── layouts/         # 布局组件
│   │   └── MainLayout.tsx        # 主布局
│   ├── pages/           # 页面组件
│   │   ├── Dashboard.tsx         # 首页仪表盘
│   │   ├── FileUpload.tsx        # 文件上传
│   │   ├── LogicLearning.tsx     # 逻辑学习
│   │   ├── FileSummary.tsx       # 文件总结
│   │   ├── LLMManagement.tsx     # 大模型管理
│   │   └── Login.tsx             # 登录页
│   ├── services/        # API 服务
│   │   └── api.ts                # API 封装
│   ├── store/           # 状态管理
│   │   ├── authStore.ts          # 认证状态
│   │   ├── chatStore.ts          # 聊天状态
│   │   └── layoutStore.ts        # 布局状态
│   ├── types/           # TypeScript 类型
│   │   └── index.ts
│   ├── utils/           # 工具函数
│   │   └── axios.ts              # Axios 配置
│   ├── App.tsx          # 根组件
│   ├── main.tsx         # 入口文件
│   └── index.css        # 全局样式
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API 集成

所有 API 调用都通过 `src/services/api.ts` 统一管理：

```typescript
// 示例：上传文件
import { fileAPI } from '@/services/api'

const handleUpload = async (formData: FormData) => {
  const response = await fileAPI.uploadFiles(formData, (progress) => {
    console.log(`上传进度: ${progress}%`)
  })
  return response.data
}
```

## 状态管理

使用 Zustand 进行状态管理：

```typescript
// 使用认证状态
import { useAuthStore } from '@/store/authStore'

const { user, isAuthenticated, login, logout } = useAuthStore()

// 使用聊天状态
import { useChatStore } from '@/store/chatStore'

const { messages, addMessage, isLoading } = useChatStore()
```

## 权限控制

```typescript
import { useAuthStore } from '@/store/authStore'

const { hasPermission } = useAuthStore()

// 检查权限
if (hasPermission('manage_models')) {
  // 显示管理功能
}
```

## 样式定制

### Grok 风格主题

所有颜色定义在 `tailwind.config.js`：

```javascript
colors: {
  grok: {
    bg: '#0A0A0A',
    surface: '#111111',
    border: '#2A2A2A',
    text: '#E5E5E5',
    textMuted: '#A0A0A0',
    accent: '#00D9FF',
    // ...
  }
}
```

### 自定义组件样式

```tsx
<div className="grok-card">
  <button className="grok-btn-primary">按钮</button>
  <input className="grok-input" />
</div>
```

## 构建生产版本

```bash
npm run build
```

构建输出在 `dist/` 目录。

## 开发规范

### 组件规范

- 使用函数组件 + Hooks
- TypeScript 严格模式
- Props 必须定义类型接口

### 命名规范

- 组件文件：PascalCase (例如 `UserProfile.tsx`)
- 工具函数：camelCase (例如 `formatDate.ts`)
- 常量：UPPER_SNAKE_CASE (例如 `API_BASE_URL`)

### 代码风格

- 使用 ESLint + Prettier
- 2 空格缩进
- 单引号字符串

## 待开发功能

- [ ] 标书生成页面完整实现
- [ ] 文件管理页面
- [ ] 用户管理页面（管理员）
- [ ] 提示词管理页面（管理员）
- [ ] 个人设置页面
- [ ] 通知系统
- [ ] 主题切换（亮色/暗色）

## 故障排除

### 开发服务器启动失败

检查端口 3000 是否被占用：

```bash
lsof -ti:3000 | xargs kill -9
```

### API 连接失败

确保后端服务正在运行：

```bash
cd ../backend
python main.py
```

### 样式不生效

重新构建 Tailwind CSS：

```bash
npm run dev
```

## 许可证

MIT License

## 联系方式

如有问题，请联系开发团队。
