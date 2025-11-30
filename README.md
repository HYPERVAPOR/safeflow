# SafeFlow - 智能测试平台接入系统

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16.0.5-black?logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-green?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.0+-blue?logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

## 项目概述

SafeFlow 是一个根据不同测试任务需求、可进行任意工具嵌入的技术和框架，提供一个智能、高效、灵活、实用的软件测试平台嵌入集成智能一体化系统。通过 LLM Agent 技术和 MCP (Model Context Protocol) 协议，实现外部测试工具的无缝接入和自动适配。

### 核心特性

- **多工具支持**：集成 Semgrep、Trivy、OWASP ZAP 等主流安全测试工具
- **智能代理**：基于 LLM Agent 的自动化测试工具调用和执行
- **统一接口**：通过 MCP 协议提供统一的工具调用接口
- **可视化界面**：提供直观的 Web 界面进行测试任务管理
- **实时监控**：支持测试任务的实时状态监控和结果展示
- **灵活配置**：支持自定义工具参数和测试策略
- **插件化架构**：基于 MCP 协议的可扩展插件系统
- **友好 UI**：采用 Monaco Editor 提供专业的代码编辑体验

## 支持的工具

| 工具 | 类型 | 描述 | 支持程度 |
|------|------|----------|------|
| **Semgrep** | 静态分析 | 代码安全漏洞和质量规则扫描 | 完全支持 |
| **Trivy** | 容器扫描 | 容器镜像和文件系统漏洞扫描 | 完全支持 |
| **OWASP ZAP** | Web安全 | Web应用程序安全扫描 | 完全支持 |

## 架构组件

### 核心 MCP 服务器
- 工具注册管理
- 参数验证
- 错误处理
- 日志记录

### 智能代理层
- 自然语言解析
- 工具选择推荐
- 参数生成优化
- 结果分析

### 多租户管理
- 工作区隔离
- 权限控制
- 资源配额
- 审计日志

### 安全监控
- FastAPI 安全中间件
- 访问控制
- 异常检测
- 性能监控

## 环境要求

### 基础依赖

- **Node.js** >= 16.0.0
- **Python** >= 3.11
- **UV** Python 包管理器（推荐替代 pip）

### 1. 克隆仓库

```bash
git clone https://github.com/HYPERVAPOR/safeflow.git
cd safeflow
```

### 2. 安装工具依赖

```bash
# 使用自动安装脚本
chmod +x scripts/install-tools-$(uname).sh
./scripts/install-tools-$(uname).sh

# 或手动安装
# 安装 Semgrep
pip install semgrep

# 安装 Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# 安装 OWASP ZAP（需要 Docker）
# 下载 ZAP Docker 镜像
```

### 3. 启动服务

#### 后端服务
```bash
cd backend
uv sync  # 等同于 pip install -r requirements.txt
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端服务
```bash
cd frontend
npm install
npm run dev
```

### 4. 访问服务

- **前端界面**: http://localhost:3000
- **MCP API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 使用流程

### 基本操作

1. **选择工具**: 从 MCP 工具列表中选择目标扫描工具
2. **配置参数**: 根据工具要求配置扫描参数和目标
3. **执行扫描**: 点击 Execute 按钮执行扫描任务
4. **查看结果**: 实时查看扫描结果和状态

### 工具使用示例

#### Semgrep 静态分析
```json
{
  "target_path": ".",
  "config": "auto",
  "severity": "ERROR",
  "output_format": "json",
  "include": ["*.py"],
  "exclude": ["**/test_*.py", "__pycache__", "*.test.js", "*.spec.ts", "node_modules", "vendor", ".git"],
  "timeout": 300
}
```

#### Trivy 漏洞扫描
```json
{
  "target": ".",
  "scan_type": "fs",
  "severity": ["MEDIUM", "HIGH", "CRITICAL"],
  "security_checks": ["vuln", "config"]
}
```

#### OWASP ZAP Web 扫描
```json
{
  "target_url": "https://httpbin.org/",
  "scan_type": "quick",
  "auth_type": "none"
}
```

### 高级功能

- **批量处理**: 支持多目标批量扫描
- **定时任务**: 支持定时扫描任务
- **报告生成**: 自动生成扫描报告
- **结果过滤**: 支持结果筛选和导出
- **历史记录**: 保存扫描历史和结果对比

## 项目结构

```
safeflow/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── mcp_tools/     # MCP 工具实现
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   ├── main.py             # 应用入口
│   └── pyproject.toml      # 项目配置
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── app/            # Next.js 应用
│   │   ├── components/     # React 组件
│   │   └── hooks/          # 自定义 Hooks
│   └── package.json        # 前端配置
├── docs/                   # 项目文档
└── scripts/                # 构建和部署脚本
```

## 核心 API 接口

### MCP 工具列表

```bash
GET /api/v1/mcp/tools
```

### 执行工具

```bash
POST /api/v1/mcp/tools/{tool_name}/execute
```

### 状态查询

```bash
GET /api/v1/mcp/status
```

## 贡献指南

我们欢迎社区贡献！

### 开发流程

1. Fork 项目
2. 创建特性分支 `git checkout -b feature/amazing-feature`
3. 提交更改 `git commit -m 'Add amazing feature'`
4. 推送分支 `git push origin feature/amazing-feature`
5. 创建 Pull Request

### 代码规范

- Python 代码遵循 PEP 8 规范
- 前端代码遵循 ESLint 和 Prettier 规范
- 提交信息遵循 Conventional Commits 规范
- 添加适当的测试和文档

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 技术致谢

- [Semgrep](https://semgrep.dev/) - 静态代码分析工具
- [Trivy](https://github.com/aquasecurity/trivy) - 容器漏洞扫描工具
- [OWASP ZAP](https://www.zaproxy.org/) - Web应用安全扫描
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) - 代码编辑器
- [Next.js](https://nextjs.org/) - React 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Python Web 框架

## 项目链接

- **GitHub 主仓库**: https://github.com/HYPERVAPOR/safeflow
- **问题反馈**: https://github.com/HYPERVAPOR/safeflow/issues
- **讨论区**: https://github.com/HYPERVAPOR/safeflow/discussions

---

<div align="center">

**SafeFlow - 让安全测试更智能、更高效**

Made with ❤️ by the SafeFlow Team

</div>