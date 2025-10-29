# SafeFlow 编排引擎使用指南

## 概述

SafeFlow 编排引擎提供基于 LangGraph 的有状态工作流管理，支持多种业务场景的自动化安全测评。

## 核心功能

- ✅ **多场景模板**：代码提交、依赖更新、紧急漏洞、版本发布
- ✅ **有状态编排**：LangGraph 驱动的工作流引擎
- ✅ **Checkpoint 支持**：断点保存和恢复
- ✅ **并行调度**：多工具并发执行
- ✅ **异步持久化**：PostgreSQL 存储
- ✅ **REST API**：完整的 HTTP 接口
- ✅ **WebSocket**：实时状态推送

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 方式1：使用初始化脚本
python scripts/init_orchestration_db.py

# 方式2：使用 Alembic
alembic upgrade head
```

### 3. 启动 API 服务

```bash
python -m safeflow.api.main
```

访问 API 文档：http://localhost:8000/docs

### 4. 运行演示

```bash
# 运行所有场景
python scripts/workflow_demo.py all

# 运行单个场景
python scripts/workflow_demo.py code_commit
```

## 编程接口

### 使用执行器

```python
import asyncio
from safeflow.orchestration.executor import WorkflowExecutor
from safeflow.orchestration.models import (
    WorkflowExecutionRequest,
    WorkflowType,
    ScanTarget
)

async def main():
    # 创建执行器
    executor = WorkflowExecutor()
    
    # 创建请求
    request = WorkflowExecutionRequest(
        workflow_type=WorkflowType.CODE_COMMIT,
        target=ScanTarget(path="/path/to/code"),
        tool_ids=["semgrep"],
        created_by="user"
    )
    
    # 执行工作流
    response = await executor.execute(request)
    
    print(f"工作流ID: {response.workflow_id}")
    print(f"状态: {response.status}")
    
    # 查询状态
    status = await executor.get_status(response.workflow_id)
    print(f"进度: {status.progress}%")
    
    # 清理
    await executor.close()

asyncio.run(main())
```

### 使用 REST API

#### 创建工作流

```bash
curl -X POST http://localhost:8000/api/orchestration/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "code_commit",
    "target": {
      "path": "/path/to/code",
      "language": "python"
    },
    "tool_ids": ["semgrep"]
  }'
```

#### 查询状态

```bash
curl http://localhost:8000/api/orchestration/workflows/{workflow_id}
```

#### 列出所有工作流

```bash
curl http://localhost:8000/api/orchestration/workflows?status=running
```

## 业务场景

### 1. 代码提交快速回归

**场景**：开发人员提交代码后触发
**工具**：Semgrep
**特点**：快速（<30分钟）、轻量级

```python
WorkflowType.CODE_COMMIT
```

### 2. 依赖更新扫描验证

**场景**：依赖库升级后触发
**工具**：Syft + Dependency-Check
**特点**：聚焦SCA、漏洞匹配

```python
WorkflowType.DEPENDENCY_UPDATE
```

### 3. 紧急漏洞披露扫描

**场景**：重大漏洞披露后触发
**工具**：所有工具并行
**特点**：高并发、快速响应（<1小时）

```python
WorkflowType.EMERGENCY_VULN
```

### 4. 版本发布全链路回归

**场景**：版本发布前触发
**工具**：所有工具
**特点**：全面、包含人工审查、生成合规报告

```python
WorkflowType.RELEASE_REGRESSION
```

## 配置

### 工作流配置

编辑 `safeflow/orchestration/config.py`：

```python
from safeflow.orchestration.config import WorkflowConfig

config = WorkflowConfig(
    retry=RetryConfig(max_retries=3),
    timeout=TimeoutConfig(workflow_timeout=3600),
    concurrency=ConcurrencyConfig(max_parallel_tools=4),
    checkpoint=CheckpointConfig(enabled=True),
    storage=StorageConfig(database_url="postgresql://...")
)
```

### 数据库配置

环境变量：

```bash
export DATABASE_URL="postgresql://safeflow:safeflow@localhost:5432/safeflow"
```

## 高级特性

### Checkpoint 和恢复

```python
# 列出 checkpoint
checkpoints = await executor.list_checkpoints(workflow_id)

# 从 checkpoint 恢复
response = await executor.resume(workflow_id, checkpoint_id)
```

### 人工审查节点

```python
# 暂停工作流
await executor.pause(workflow_id)

# 人工审查后恢复
await executor.resume(workflow_id)
```

### WebSocket 实时更新

```javascript
const ws = new WebSocket('ws://localhost:8000/api/orchestration/workflows/{workflow_id}/stream');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Progress:', data.progress);
};
```

## 架构

```
┌─────────────────────────────────────────────┐
│           FastAPI REST API                  │
│  (orchestration.py, main.py)               │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│        WorkflowExecutor                     │
│  整合引擎、调度器、存储                      │
└─────────────┬───────────────────────────────┘
              │
       ┌──────┴──────┬──────────────┬─────────┐
       │             │              │         │
┌──────▼──────┐ ┌───▼────┐ ┌───────▼──┐ ┌────▼────┐
│   Engine    │ │Scheduler│ │ Storage  │ │Templates│
│  (LangGraph)│ │ (Async) │ │(PostgreSQL)│ │(4场景) │
└──────┬──────┘ └────────┘ └──────────┘ └─────────┘
       │
┌──────▼──────────────────────────────────────┐
│         Workflow Nodes (8个节点)            │
│  initialize, scan, collect, validate, ...  │
└─────────────────────────────────────────────┘
```

## 性能指标

- **中型项目（30万行代码）**：6小时内完成
- **并行工具调度**：节省50%时间
- **Checkpoint恢复**：<5分钟
- **单漏洞验证**：<10分钟

## 故障排除

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 创建数据库
createdb safeflow
```

### LangGraph 不可用

系统会自动降级到简化模式，功能不受影响。

### 工具未安装

```bash
# 安装 Semgrep
pip install semgrep

# 安装 Syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh
```

## 更多资源

- [PRD 文档](./PRD.md)
- [API 文档](http://localhost:8000/docs)
- [GitHub 仓库](#)

## 反馈和贡献

欢迎提交 Issue 和 Pull Request！

