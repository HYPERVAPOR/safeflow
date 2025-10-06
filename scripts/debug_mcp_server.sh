#!/bin/bash
#
# MCP Server 调试脚本
#

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              SafeFlow MCP Server 调试工具                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "🔍 调试信息:"
echo "   当前目录: $(pwd)"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   Python 版本: $(python3 --version)"
echo ""

# 检查依赖
echo "📦 检查依赖..."

python3 -c "
import sys
print(f'Python 路径: {sys.executable}')

try:
    import mcp
    print('✅ MCP SDK 已安装')
except ImportError as e:
    print(f'❌ MCP SDK 未安装: {e}')
    sys.exit(1)

try:
    import safeflow.mcp.server
    print('✅ SafeFlow MCP Server 模块可导入')
except ImportError as e:
    print(f'❌ SafeFlow MCP Server 模块导入失败: {e}')
    sys.exit(1)

try:
    from safeflow.adapters.semgrep_adapter import SemgrepAdapter
    print('✅ Semgrep 适配器可导入')
except ImportError as e:
    print(f'❌ Semgrep 适配器导入失败: {e}')

try:
    from safeflow.adapters.syft_adapter import SyftAdapter
    print('✅ Syft 适配器可导入')
except ImportError as e:
    print(f'❌ Syft 适配器导入失败: {e}')
"

if [ $? -ne 0 ]; then
    echo "❌ 依赖检查失败，请修复上述问题"
    exit 1
fi

echo ""

# 测试 MCP Server 启动
echo "🧪 测试 MCP Server 启动..."

# 创建测试输入
TEST_INPUT=$(mktemp)
cat > "$TEST_INPUT" << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"debug-test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF

echo "测试输入:"
cat "$TEST_INPUT"
echo ""

echo "启动 MCP Server 并发送测试请求..."
echo "----------------------------------------"

# 启动服务器并发送测试请求
timeout 10s python3 -m safeflow.mcp.server < "$TEST_INPUT"

echo ""
echo "----------------------------------------"
echo "测试完成"

# 清理
rm -f "$TEST_INPUT"

echo ""
echo "💡 如果看到 JSON 响应，说明 MCP Server 工作正常"
echo "   如果出现错误，请检查上述输出"
