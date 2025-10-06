# SafeFlow - 软件代码安全测评智能编排平台

## 项目简介

SafeFlow 是一个基于模型上下文协议（MCP）的软件代码安全测评工具集成与智能编排平台。通过统一的协议标准，实现多种异构安全工具的快速接入、结果融合和智能编排。

### 核心特性

- 🔌 **统一接入**：基于 MCP 协议，实现安全工具的即插即用
- 🔄 **结果融合**：跨工具检测结果聚合、去重和优先级排序
- 🎯 **智能编排**：场景驱动的动态工作流调度
- 📊 **覆盖增强**：智能化测试用例生成，提升检测覆盖率
- ✅ **自动验证**：行为差异分析，降低误报率
- 🔗 **证据链**：全流程可追溯的证据记录

## 当前状态

**第一阶段（MVP）正在开发中**

已完成：
- ✅ MCP 协议规范设计
- ✅ 工具适配器框架
- ✅ Semgrep（SAST）适配器实现
- 🔄 项目基础架构搭建（进行中）

待完成：
- ⏳ Syft（SCA）适配器实现
- ⏳ 数据存储模块
- ⏳ API 接口开发
- ⏳ 端到端集成测试

## 快速开始

### 环境要求

- Python 3.10+
- PostgreSQL 12+（可选，用于数据持久化）
- Git

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/your-org/SafeFlow.git
cd SafeFlow
```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **安装安全工具**

```bash
# 安装 Semgrep
pip install semgrep

# 安装 Syft（下载对应平台的二进制文件）
# Linux
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# 或直接从 GitHub Releases 下载
# https://github.com/anchore/syft/releases
```

5. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

6. **初始化数据库（可选）**

```bash
python scripts/init_db.py
```

### 运行测试

```bash
# 测试 Semgrep 适配器
python -m pytest tests/test_adapters/test_semgrep.py -v

# 运行所有测试
python -m pytest tests/ -v
```

### 快速体验

#### 方式 1: 直接调用（快速开始）

```bash
# 运行简单的扫描示例
python scripts/quick_scan_demo.py /path/to/your/code
```

#### 方式 2: MCP 服务化调用

```bash
# 使用 MCP 风格的服务层（支持服务发现、统一接口、结果聚合）
python scripts/mcp_service_demo.py /path/to/your/code
```

#### 方式 3: 真正的 MCP 协议（与 LLM 集成）✨

```bash
# 首先安装 MCP SDK
pip install mcp[cli]

# 使用标准 MCP 协议（JSON-RPC 2.0）
python scripts/mcp_protocol_demo.py /path/to/your/code
```

**三种方式对比**：
- 方式 1: 直接调用 - 适合学习和快速测试
- 方式 2: 服务层 - 适合 Python 应用集成
- 方式 3: MCP 协议 - 适合 LLM 集成（Claude Desktop 等）

详细说明：[docs/MCP_COMPLETE_GUIDE.md](docs/MCP_COMPLETE_GUIDE.md)

## 项目结构

```
SafeFlow/
├── docs/                      # 文档
│   ├── PRD.md                 # 产品需求文档
│   ├── DEV_PLAN.md            # 开发计划
│   ├── mcp_protocol_spec.md   # MCP 协议规范
│   └── MCP_COMPLETE_GUIDE.md  # MCP 完整指南
│
├── safeflow/                  # 主应用
│   ├── schemas/               # MCP Schema 定义
│   │   ├── tool_capability.py
│   │   └── vulnerability.py
│   ├── adapters/              # 工具适配器
│   │   ├── base.py
│   │   ├── semgrep_adapter.py
│   │   └── syft_adapter.py
│   ├── models/                # 数据库模型（待实现）
│   ├── services/              # 业务逻辑（待实现）
│   └── api/                   # API 接口（待实现）
│
├── tests/                     # 测试
├── scripts/                   # 工具脚本
├── requirements.txt           # 依赖清单
└── README.md                  # 本文件
```

## MCP 协议概述

模型上下文协议（Model Context Protocol, MCP）是 SafeFlow 的核心，它定义了：

### 1. 工具能力声明（Tool Capability）

描述工具的"身份证"，包括：
- 工具元信息（名称、版本、类型）
- 支持的语言和检测能力
- 输入要求和输出格式
- 执行配置和资源需求

### 2. 统一漏洞模型（Unified Vulnerability）

所有工具的检测结果映射到统一格式：
- 漏洞类型（基于 CWE/OWASP）
- 位置信息（文件、函数、行号）
- 严重度和置信度
- 来源工具和原始数据
- 验证状态

### 3. 适配器接口规范

每个适配器实现四个核心方法：
- `get_capability()`: 返回工具能力声明
- `validate_input()`: 验证输入
- `execute()`: 执行扫描
- `parse_output()`: 转换为统一格式

详细规范请参考：[docs/mcp_protocol_spec.md](docs/mcp_protocol_spec.md)

## 开发指南

### 添加新的工具适配器

1. 在 `safeflow/adapters/` 下创建新文件，如 `mytool_adapter.py`
2. 继承 `BaseAdapter` 类
3. 实现四个抽象方法
4. 定义工具能力声明
5. 实现输出解析逻辑（映射到统一漏洞模型）

示例代码：

```python
from safeflow.adapters.base import BaseAdapter
from safeflow.schemas.tool_capability import ToolCapability
from safeflow.schemas.vulnerability import UnifiedVulnerability

class MyToolAdapter(BaseAdapter):
    def get_capability(self) -> ToolCapability:
        # 返回工具能力声明
        pass
    
    def validate_input(self, scan_request):
        # 验证输入
        pass
    
    def execute(self, scan_request):
        # 调用工具执行扫描
        pass
    
    def parse_output(self, raw_output, scan_request):
        # 解析并转换输出
        pass
```

### 运行代码检查

```bash
# 代码格式化
black safeflow/

# 类型检查
mypy safeflow/

# 代码风格检查
flake8 safeflow/
```

## 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目主页：https://github.com/your-org/SafeFlow
- 问题反馈：https://github.com/your-org/SafeFlow/issues
- 文档：https://safeflow.readthedocs.io

## 致谢

感谢以下开源项目和工具：
- [Semgrep](https://semgrep.dev/) - 静态代码分析
- [Syft](https://github.com/anchore/syft) - 软件成分分析
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 工作流编排

---

**注意**：本项目当前处于早期开发阶段，API 和功能可能会发生变化。

