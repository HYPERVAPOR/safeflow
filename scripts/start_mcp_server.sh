#!/bin/bash
#
# SafeFlow MCP Server 启动脚本
#

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          启动 SafeFlow MCP Server                         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

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

echo "✅ 环境检查通过"
echo ""
echo "🚀 启动 MCP Server..."
echo "   监听方式: stdio"
echo "   协议: JSON-RPC 2.0"
echo ""
echo "💡 提示: 服务器将等待客户端连接"
echo "   使用 Ctrl+C 停止服务器"
echo ""

# 启动服务器
cd "$(dirname "$0")/.."
python3 -m safeflow.mcp.server

