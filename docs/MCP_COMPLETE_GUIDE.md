# SafeFlow MCP 完整指南

## 📖 概述

SafeFlow 支持**真正的 MCP (Model Context Protocol) 协议**，基于官方 MCP Python SDK 实现。MCP 是由 Anthropic 开发的开放协议，让 AI 模型（如 Claude）能够安全地与外部工具交互。

**官方文档**：https://modelcontextprotocol.io

---

## 🚀 快速开始

### 1. 环境设置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install semgrep

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### 2. 测试 MCP Server

```bash
# 测试启动
python -m safeflow.mcp.server
```

### 3. 运行演示

```bash
# 完整演示
python scripts/mcp_protocol_demo.py ./safeflow

# 交互式测试
python scripts/test_mcp_client.py
```

---

## 🔧 MCP Server 功能

### 注册的 MCP Tools

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `scan_with_semgrep` | Semgrep 静态分析 | `target_path`, `rules`, `scan_id` |
| `scan_with_syft` | Syft 成分分析 | `target_path`, `scan_id` |
| `scan_with_all_tools` | 全工具扫描 | `target_path`, `scan_id` |
| `get_tool_capability` | 查询工具能力 | `tool_name` |
| `list_available_tools` | 列出可用工具 | 无 |

### 注册的 MCP Resources

| 资源 URI | 功能 |
|----------|------|
| `scan://results/{scan_id}` | 访问扫描结果 |
| `scan://history` | 访问扫描历史 |

---

## 🧪 测试方法

### 方法 1: Python 客户端（推荐）

```bash
python scripts/test_mcp_client.py
```

**功能菜单**：
1. 列出所有可用工具
2. 查询工具能力
3. 执行 Semgrep 扫描
4. 执行 Syft 扫描
5. 执行全工具扫描
6. 查看扫描历史
7. 读取扫描结果
8. 运行完整测试套件

### 方法 2: HTTP 代理

```bash
# 启动代理服务器
python scripts/mcp_http_proxy.py

# 使用 curl 测试
curl http://localhost:8000/tools
curl -X POST http://localhost:8000/scan/semgrep \
  -H "Content-Type: application/json" \
  -d '{"target_path": "./safeflow"}'
```

### 方法 3: MCP Inspector

```bash
# 安装并启动
npm install -g @modelcontextprotocol/inspector
npx @modelcontextprotocol/inspector python -m safeflow.mcp.server

# 在浏览器访问 http://localhost:3000
```

### 方法 4: 直接 JSON-RPC

```bash
# 测试初始化
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"test","version":"1.0"}}}' | python -m safeflow.mcp.server

# 列出工具
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python -m safeflow.mcp.server
```

---

## 🤖 与 Claude Desktop 集成

### 1. 配置 Claude Desktop

编辑配置文件：

**macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "safeflow": {
      "command": "python",
      "args": ["-m", "safeflow.mcp.server"],
      "env": {
        "PYTHONPATH": "/home/hv/projs/SafeFlow"
      }
    }
  }
}
```

### 2. 重启 Claude Desktop

重启后，Claude 将自动连接到 SafeFlow MCP Server。

### 3. 在 Claude 中使用

**示例对话**：

> 你: 请使用 SafeFlow 扫描这个项目：/path/to/my/project

> Claude: 好的，我将使用 SafeFlow 的安全扫描工具。[调用 scan_with_all_tools]
> 
> 扫描完成！发现以下问题：
> - 2个严重漏洞
> - 5个高危问题
> - 15个软件包依赖

---

## 🔌 协议通信

### JSON-RPC 2.0 消息格式

**请求示例**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "scan_with_semgrep",
    "arguments": {
      "target_path": "/path/to/code",
      "rules": "auto"
    }
  }
}
```

**响应示例**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\": true, \"vulnerability_count\": 5, ...}"
    }]
  }
}
```

### 传输方式

- ✅ **stdio**: 标准输入/输出（默认）
- 🔄 **HTTP/SSE**: 可扩展支持

---

## 🆚 三种调用方式对比

| 特性 | 直接调用 | 服务层 | **MCP 协议** ✨ |
|-----|---------|--------|--------------|
| 标准化 | 低 | 中 | **高** |
| 跨语言 | ❌ | ❌ | **✅** |
| LLM 集成 | ❌ | ❌ | **✅** |
| 协议 | 无 | 自定义 | **JSON-RPC 2.0** |
| 适用场景 | 学习测试 | Python 应用 | **LLM 集成** |

---

## 🐛 故障排查

### 常见问题

#### 1. 虚拟环境问题

**错误**：`ImportError: No module named 'safeflow'`

**解决**：
```bash
# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

#### 2. MCP SDK 未安装

**错误**：`ImportError: No module named 'mcp'`

**解决**：
```bash
pip install mcp[cli]
```

#### 3. 依赖冲突

**错误**：`httpx==0.26.0 and mcp have conflicting dependencies`

**解决**：已在 requirements.txt 中修复，使用 `httpx>=0.27.0`

#### 4. MCP Inspector 连接失败

**错误**：`Connection Error - Check if your MCP server is running`

**解决**：
```bash
# 1. 测试 MCP Server
python -m safeflow.mcp.server

# 2. 检查路径配置
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 3. 使用正确的启动命令
npx @modelcontextprotocol/inspector python -m safeflow.mcp.server
```

### 调试技巧

#### 1. 启用详细日志

```bash
export LOG_LEVEL=DEBUG
python -m safeflow.mcp.server
```

#### 2. 检查进程状态

```bash
# 查看 MCP 相关进程
ps aux | grep mcp

# 查看端口占用
netstat -tlnp | grep -E "(3000|8000)"
```

#### 3. 测试网络连接

```bash
# 测试 HTTP 代理
curl -v http://localhost:8000/health

# 测试 MCP Inspector
curl -v http://localhost:3000
```

---

## 📊 性能指标

### 当前性能

- ✅ **连接开销**: 首次连接 ~100ms
- ✅ **工具调用**: 取决于扫描工具（秒到分钟）
- ✅ **资源读取**: 毫秒级
- ✅ **并发支持**: 异步 I/O

### 限制

- ⚠️ **传输方式**: 仅支持 stdio（未来可扩展 HTTP/SSE）
- ⚠️ **认证**: 无（适合本地使用）
- ⚠️ **路径限制**: 无白名单（需要生产环境添加）
- ⚠️ **资源限制**: 无超时和大小限制（需要添加）

---

## 🔒 安全考虑

### 生产环境建议

1. **路径访问控制**
```python
ALLOWED_PATHS = ["/home/user/projects"]
```

2. **认证和授权**
```python
# 添加 API 密钥验证
# 添加用户权限检查
```

3. **资源限制**
```python
MAX_SCAN_TIME = 600  # 10分钟
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

4. **审计日志**
```python
# 记录所有工具调用
# 记录资源访问
```

---

## 🚀 未来规划

### 短期（1-2周）

- [ ] 添加更多安全工具（OWASP ZAP, Bandit 等）
- [ ] 实现 HTTP/SSE 传输支持
- [ ] 添加路径白名单和访问控制
- [ ] 完善错误处理和日志

### 中期（1个月）

- [ ] 实现认证和授权机制
- [ ] 添加资源限制和超时控制
- [ ] 支持批量扫描和队列
- [ ] 实现结果持久化存储

### 长期（3个月）

- [ ] 构建 Web UI 管理界面
- [ ] 支持分布式部署
- [ ] 与更多 LLM 平台集成
- [ ] 实现高级安全分析功能

---

## 📚 相关资源

- **MCP 官方文档**: https://modelcontextprotocol.io
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **MCP 规范**: https://spec.modelcontextprotocol.io
- **Claude Desktop**: https://claude.ai/desktop

---

## 🎯 总结

SafeFlow 现在是一个**完整的 MCP 协议实现**，具备：

1. ✅ **标准 MCP 协议支持**（JSON-RPC 2.0）
2. ✅ **5 个 MCP Tools**（安全扫描工具）
3. ✅ **2 个 MCP Resources**（结果和历史）
4. ✅ **完整的 Client/Server 实现**
5. ✅ **Claude Desktop 集成支持**
6. ✅ **多种测试方法**
7. ✅ **详细的故障排查指南**

**关键成就**:
- 从"机械调用 CLI"演进到"标准 MCP 协议"
- 实现了真正的 LLM 可调用的安全工具
- 为未来的智能化安全分析奠定了基础

现在你可以：
- ✅ 通过标准 MCP 协议调用安全工具
- ✅ 在 Claude Desktop 中直接使用
- ✅ 让 LLM 自动进行安全分析
- ✅ 构建智能化的安全工作流

---

**文档版本**: v1.0  
**最后更新**: 2025-01-15  
**维护者**: SafeFlow 开发团队
