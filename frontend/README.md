# SafeFlow Frontend

基于 LLM Agent 的智能测试平台接入系统前端应用。

## 技术栈

- **Next.js 15** - React 全栈框架
- **TypeScript** - 类型安全的 JavaScript
- **Tailwind CSS** - 实用优先的 CSS 框架
- **ESLint** - 代码质量检查

## 项目结构

```
frontend/
├── src/
│   ├── app/              # App Router 页面和布局
│   │   ├── globals.css   # 全局样式
│   │   ├── layout.tsx    # 根布局
│   │   └── page.tsx      # 主页面
│   ├── components/       # 可复用组件
│   │   ├── Loading.tsx   # 加载组件
│   │   └── ErrorDisplay.tsx # 错误显示组件
│   ├── hooks/            # 自定义 React Hooks
│   │   └── useApi.ts     # API 调用 Hook
│   ├── lib/              # 工具库
│   │   └── api.ts        # API 客户端
│   └── types/            # TypeScript 类型定义
├── public/               # 静态资源
├── package.json          # 项目配置
├── tsconfig.json         # TypeScript 配置
├── tailwind.config.js    # Tailwind CSS 配置
├── next.config.js        # Next.js 配置
└── README.md             # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:3000 启动。

### 3. 构建生产版本

```bash
npm run build
npm start
```

## 功能模块

### 🏠 主页
- 系统概览和功能导航
- 快速访问各个功能模块

### 🛠️ 工具管理
- 查看和管理测试工具
- 工具状态监控
- 工具能力配置

### 📋 任务管理
- 创建新的测试任务
- 监控任务执行状态
- 任务历史记录

### 📊 结果分析
- 查看测试结果
- 结果融合和分析
- 报告生成

### ⚙️ 系统集成
- CI/CD 集成配置
- Webhook 设置
- 自定义规则管理

## 开发指南

### 添加新页面

在 `src/app/` 目录下创建新的路由文件：

```tsx
// src/app/tools/page.tsx
export default function ToolsPage() {
  return (
    <div>
      <h1>工具管理</h1>
      {/* 页面内容 */}
    </div>
  );
}
```

### API 调用

使用 `src/lib/api.ts` 中的 API 客户端：

```tsx
import { apiClient } from '@/lib/api';
import { useApi } from '@/hooks/useApi';

// 在组件中使用
const { data, loading, error } = useApi(() => apiClient.get('/tools'));
```

### 样式规范

使用 Tailwind CSS 进行样式开发：

```tsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h2 className="text-xl font-semibold text-gray-900 mb-4">
    标题
  </h2>
  <p className="text-gray-600">内容</p>
</div>
```

## 构建和部署

### 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Docker 部署

```dockerfile
FROM node:18-alpine AS base

# 安装依赖
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# 构建应用
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# 生产运行
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

## 代码质量

运行 ESLint 检查：

```bash
npm run lint
```

运行 TypeScript 类型检查：

```bash
npm run type-check
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

ISC License