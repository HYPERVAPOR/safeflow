#!/bin/bash
#
# 使用 curl 直接测试 MCP JSON-RPC 协议
#

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           使用 curl 测试 MCP JSON-RPC 协议                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查 curl
if ! command -v curl &> /dev/null; then
    echo "❌ 错误: curl 未安装"
    echo "   请安装: sudo apt-get install curl"
    exit 1
fi

# 检查 jq（可选，用于格式化 JSON）
if ! command -v jq &> /dev/null; then
    echo "⚠️  警告: jq 未安装，JSON 输出将不会被格式化"
    echo "   建议安装: sudo apt-get install jq"
    JQ_CMD="cat"
else
    JQ_CMD="jq ."
    echo "✅ jq 已安装，JSON 输出将被格式化"
fi

echo ""

# 创建临时文件存储请求
TEMP_DIR=$(mktemp -d)
REQUEST_FILE="$TEMP_DIR/request.json"
RESPONSE_FILE="$TEMP_DIR/response.json"

# 清理函数
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "📝 测试 1: 初始化 MCP 会话"
echo "----------------------------------------"

cat > "$REQUEST_FILE" << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "clientInfo": {
      "name": "curl-test-client",
      "version": "1.0.0"
    }
  }
}
EOF

echo "请求:"
cat "$REQUEST_FILE" | $JQ_CMD
echo ""

echo "发送请求到 MCP Server..."
echo "python -m safeflow.mcp.server < $REQUEST_FILE"
echo ""

# 注意：这个测试需要手动运行，因为需要 stdio 通信
echo "💡 手动测试步骤:"
echo "1. 在一个终端启动 MCP Server:"
echo "   python -m safeflow.mcp.server"
echo ""
echo "2. 在另一个终端发送请求:"
echo "   echo '$(cat $REQUEST_FILE)' | python -m safeflow.mcp.server"
echo ""

echo "📝 测试 2: 列出工具"
echo "----------------------------------------"

cat > "$REQUEST_FILE" << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
EOF

echo "请求:"
cat "$REQUEST_FILE" | $JQ_CMD
echo ""

echo "📝 测试 3: 调用工具"
echo "----------------------------------------"

cat > "$REQUEST_FILE" << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "list_available_tools",
    "arguments": {}
  }
}
EOF

echo "请求:"
cat "$REQUEST_FILE" | $JQ_CMD
echo ""

echo "📝 测试 4: 调用扫描工具"
echo "----------------------------------------"

cat > "$REQUEST_FILE" << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "scan_with_semgrep",
    "arguments": {
      "target_path": "./safeflow",
      "rules": "auto"
    }
  }
}
EOF

echo "请求:"
cat "$REQUEST_FILE" | $JQ_CMD
echo ""

echo "📝 测试 5: 列出资源"
echo "----------------------------------------"

cat > "$REQUEST_FILE" << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/list",
  "params": {}
}
EOF

echo "请求:"
cat "$REQUEST_FILE" | $JQ_CMD
echo ""

echo "📝 测试 6: 读取资源"
echo "----------------------------------------"

cat > "$REQUEST_FILE" << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "resources/read",
  "params": {
    "uri": "scan://history"
  }
}
EOF

echo "请求:"
cat "$REQUEST_FILE" | $JQ_CMD
echo ""

echo "🚀 自动化测试脚本"
echo "----------------------------------------"

cat > "$TEMP_DIR/auto_test.sh" << 'EOF'
#!/bin/bash

# 自动化 MCP 测试脚本
echo "开始自动化 MCP 测试..."

# 测试 1: 初始化
echo "测试 1: 初始化"
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"auto-test","version":"1.0"}}}' | python -m safeflow.mcp.server

# 测试 2: 列出工具
echo "测试 2: 列出工具"
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python -m safeflow.mcp.server

# 测试 3: 调用工具
echo "测试 3: 调用工具"
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_available_tools","arguments":{}}}' | python -m safeflow.mcp.server

echo "测试完成!"
EOF

chmod +x "$TEMP_DIR/auto_test.sh"

echo "已生成自动化测试脚本: $TEMP_DIR/auto_test.sh"
echo ""
echo "运行自动化测试:"
echo "  $TEMP_DIR/auto_test.sh"
echo ""

echo "📚 更多测试方法"
echo "----------------------------------------"
echo "1. 使用 Python 客户端: python scripts/test_mcp_client.py"
echo "2. 使用 MCP Inspector: bash scripts/test_mcp_inspector.sh"
echo "3. 使用演示脚本: python scripts/mcp_protocol_demo.py ./safeflow"
echo "4. 手动 stdio 测试: echo 'JSON' | python -m safeflow.mcp.server"
echo ""

echo "💡 提示:"
echo "- MCP 使用 stdio 通信，不是 HTTP"
echo "- 需要将 JSON 通过标准输入发送给服务器"
echo "- 服务器会通过标准输出返回 JSON 响应"
echo ""

echo "🔗 参考文档:"
echo "- MCP 协议规范: https://spec.modelcontextprotocol.io"
echo "- SafeFlow MCP 指南: docs/MCP_PROTOCOL_GUIDE.md"
