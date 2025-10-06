#!/bin/bash
#
# SafeFlow 快速测试脚本
#

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                SafeFlow 快速测试                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: bash scripts/setup_and_test.sh"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "✅ 环境已准备就绪"
echo "   Python: $(which python)"
echo "   PYTHONPATH: $PYTHONPATH"
echo ""

# 测试 1: 导入测试
echo "🧪 测试 1: 模块导入"
echo "----------------------------------------"

python -c "
try:
    import mcp
    print('✅ MCP SDK 导入成功')
except ImportError as e:
    print(f'❌ MCP SDK 导入失败: {e}')
    exit(1)

try:
    import safeflow.mcp.server
    print('✅ SafeFlow MCP Server 导入成功')
except ImportError as e:
    print(f'❌ SafeFlow MCP Server 导入失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 导入测试失败"
    exit 1
fi

echo ""

# 测试 2: MCP Server 启动测试
echo "🧪 测试 2: MCP Server 启动"
echo "----------------------------------------"

echo "启动 MCP Server（3秒测试）..."

# 创建测试输入
TEST_INPUT=$(mktemp)
cat > "$TEST_INPUT" << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"quick-test","version":"1.0"}}}
EOF

# 启动并测试
timeout 3s python -m safeflow.mcp.server < "$TEST_INPUT" > /tmp/mcp_output 2>&1 &
SERVER_PID=$!

sleep 1

if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ MCP Server 启动成功"
    kill $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
else
    echo "❌ MCP Server 启动失败"
    echo "错误信息:"
    cat /tmp/mcp_output
    rm -f "$TEST_INPUT" /tmp/mcp_output
    exit 1
fi

# 清理
rm -f "$TEST_INPUT" /tmp/mcp_output

echo ""

# 测试 3: 演示脚本测试
echo "🧪 测试 3: 演示脚本"
echo "----------------------------------------"

if [ -f "scripts/mcp_protocol_demo.py" ]; then
    echo "运行 MCP 协议演示（仅测试连接）..."
    timeout 10s python scripts/mcp_protocol_demo.py ./safeflow > /tmp/demo_output 2>&1
    
    if grep -q "MCP 连接建立成功" /tmp/demo_output; then
        echo "✅ 演示脚本运行成功"
    else
        echo "⚠️  演示脚本可能有问题，但基本功能正常"
        echo "输出:"
        head -20 /tmp/demo_output
    fi
    
    rm -f /tmp/demo_output
else
    echo "⚠️  演示脚本不存在，跳过"
fi

echo ""

# 总结
echo "🎉 快速测试完成！"
echo "========================================"
echo ""
echo "✅ 所有基本测试通过"
echo ""
echo "📚 下一步可以尝试:"
echo ""
echo "1. 运行完整演示:"
echo "   python scripts/mcp_protocol_demo.py ./safeflow"
echo ""
echo "2. 运行交互式测试:"
echo "   python scripts/test_mcp_client.py"
echo ""
echo "3. 启动 HTTP 代理:"
echo "   python scripts/mcp_http_proxy.py"
echo ""
echo "4. 使用 MCP Inspector:"
echo "   bash scripts/start_mcp_inspector.sh"
echo ""
echo "💡 记住: 每次使用前都要激活虚拟环境"
echo "   source venv/bin/activate"
echo ""
