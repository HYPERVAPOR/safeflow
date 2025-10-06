#!/bin/bash
#
# 使用 MCP Inspector 测试 SafeFlow MCP Server
#

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        使用 MCP Inspector 测试 SafeFlow MCP Server        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: Node.js 未安装"
    echo "   请安装 Node.js:"
    echo "   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "   sudo apt-get install -y nodejs"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: npm 未安装"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"
echo ""

# 安装 MCP Inspector
echo "📦 安装 MCP Inspector..."
npm install -g @modelcontextprotocol/inspector

if [ $? -ne 0 ]; then
    echo "❌ 安装失败，尝试使用 npx 运行..."
    echo ""
    echo "🚀 启动 MCP Inspector（使用 npx）..."
    echo "   服务器: python -m safeflow.mcp.server"
    echo "   浏览器: http://localhost:3000"
    echo ""
    echo "💡 提示: 在 WSL 中，你需要在 Windows 浏览器中访问"
    echo "   http://localhost:3000"
    echo ""
    
    # 使用 npx 运行
    npx @modelcontextprotocol/inspector python -m safeflow.mcp.server
else
    echo "✅ MCP Inspector 安装成功"
    echo ""
    echo "🚀 启动 MCP Inspector..."
    echo "   服务器: python -m safeflow.mcp.server"
    echo "   浏览器: http://localhost:3000"
    echo ""
    echo "💡 提示: 在 WSL 中，你需要在 Windows 浏览器中访问"
    echo "   http://localhost:3000"
    echo ""
    
    # 使用全局安装的版本
    mcp-inspector python -m safeflow.mcp.server
fi
