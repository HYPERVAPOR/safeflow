#!/bin/bash
#
# 可靠的 MCP Inspector 启动脚本
#

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        启动 SafeFlow MCP Inspector（调试版）              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查环境
echo "🔍 检查环境..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python 3 未安装"
    exit 1
fi

# 检查 MCP SDK
python3 -c "import mcp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 错误: MCP SDK 未安装"
    echo "   请运行: pip install mcp[cli]"
    exit 1
fi

# 检查 SafeFlow 模块
python3 -c "import safeflow.mcp.server" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 错误: SafeFlow MCP Server 模块不可用"
    echo "   请确保在 SafeFlow 项目根目录运行此脚本"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "📝 设置 PYTHONPATH: $PYTHONPATH"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: Node.js 未安装"
    echo "   请安装 Node.js:"
    echo "   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "   sudo apt-get install -y nodejs"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo ""

# 测试 MCP Server 是否能启动
echo "🧪 测试 MCP Server 启动..."
timeout 5s python3 -m safeflow.mcp.server &
SERVER_PID=$!
sleep 2

if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ MCP Server 可以正常启动"
    kill $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
else
    echo "❌ MCP Server 启动失败"
    echo "   请检查错误信息并修复"
    exit 1
fi

echo ""

# 安装 MCP Inspector
echo "📦 安装 MCP Inspector..."
if ! npm list -g @modelcontextprotocol/inspector &> /dev/null; then
    echo "正在安装 MCP Inspector..."
    npm install -g @modelcontextprotocol/inspector
    if [ $? -ne 0 ]; then
        echo "❌ 安装失败，尝试使用 npx..."
        USE_NPX=true
    else
        echo "✅ MCP Inspector 安装成功"
        USE_NPX=false
    fi
else
    echo "✅ MCP Inspector 已安装"
    USE_NPX=false
fi

echo ""

# 创建启动配置
echo "📝 创建 MCP Inspector 配置..."

# 获取当前目录的绝对路径
CURRENT_DIR=$(pwd)
PYTHON_CMD=$(which python3)

echo "当前目录: $CURRENT_DIR"
echo "Python 命令: $PYTHON_CMD"

# 创建临时配置文件
TEMP_CONFIG=$(mktemp)
cat > "$TEMP_CONFIG" << EOF
{
  "mcpServers": {
    "safeflow": {
      "command": "$PYTHON_CMD",
      "args": [
        "-m",
        "safeflow.mcp.server"
      ],
      "env": {
        "PYTHONPATH": "$CURRENT_DIR"
      }
    }
  }
}
EOF

echo "配置文件: $TEMP_CONFIG"
echo "配置内容:"
cat "$TEMP_CONFIG"
echo ""

# 启动 MCP Inspector
echo "🚀 启动 MCP Inspector..."
echo "   服务器命令: $PYTHON_CMD -m safeflow.mcp.server"
echo "   工作目录: $CURRENT_DIR"
echo "   浏览器地址: http://localhost:3000"
echo ""
echo "💡 提示:"
echo "   1. 在 WSL 中，在 Windows 浏览器访问 http://localhost:3000"
echo "   2. 如果连接失败，检查终端中的错误信息"
echo "   3. 按 Ctrl+C 停止服务器"
echo ""

if [ "$USE_NPX" = true ]; then
    echo "使用 npx 启动..."
    npx @modelcontextprotocol/inspector --config "$TEMP_CONFIG"
else
    echo "使用全局安装版本启动..."
    mcp-inspector --config "$TEMP_CONFIG"
fi

# 清理临时文件
rm -f "$TEMP_CONFIG"
