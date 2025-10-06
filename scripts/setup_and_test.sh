#!/bin/bash
#
# SafeFlow 完整设置和测试脚本
#

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           SafeFlow 完整设置和测试脚本                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查是否在项目根目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在 SafeFlow 项目根目录运行此脚本"
    exit 1
fi

echo "📁 当前目录: $(pwd)"
echo ""

# 步骤 1: 创建虚拟环境
echo "🔧 步骤 1: 创建虚拟环境"
echo "----------------------------------------"

if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 步骤 2: 激活虚拟环境
echo ""
echo "🔧 步骤 2: 激活虚拟环境"
echo "----------------------------------------"

source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

echo "✅ 虚拟环境已激活"
echo "   Python 路径: $(which python)"
echo "   Python 版本: $(python --version)"

# 步骤 3: 升级 pip
echo ""
echo "🔧 步骤 3: 升级 pip"
echo "----------------------------------------"

python -m pip install --upgrade pip
echo "✅ pip 升级完成"

# 步骤 4: 安装依赖
echo ""
echo "🔧 步骤 4: 安装依赖"
echo "----------------------------------------"

echo "安装 requirements.txt 中的依赖..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    echo "尝试单独安装关键依赖..."
    
    echo "安装 MCP SDK..."
    pip install mcp[cli]
    
    echo "安装 Pydantic..."
    pip install pydantic
    
    echo "安装 Loguru..."
    pip install loguru
    
    echo "安装 FastAPI..."
    pip install fastapi uvicorn
fi

echo "✅ 依赖安装完成"

# 步骤 5: 安装安全工具
echo ""
echo "🔧 步骤 5: 安装安全工具"
echo "----------------------------------------"

echo "安装 Semgrep..."
pip install semgrep

if [ $? -ne 0 ]; then
    echo "⚠️  Semgrep 安装失败，但可以继续测试"
else
    echo "✅ Semgrep 安装成功"
fi

# 步骤 6: 设置环境变量
echo ""
echo "🔧 步骤 6: 设置环境变量"
echo "----------------------------------------"

export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "✅ PYTHONPATH 已设置: $PYTHONPATH"

# 步骤 7: 测试导入
echo ""
echo "🔧 步骤 7: 测试模块导入"
echo "----------------------------------------"

python -c "
import sys
print(f'Python 路径: {sys.executable}')

try:
    import mcp
    print('✅ MCP SDK 导入成功')
except ImportError as e:
    print(f'❌ MCP SDK 导入失败: {e}')

try:
    import safeflow.mcp.server
    print('✅ SafeFlow MCP Server 导入成功')
except ImportError as e:
    print(f'❌ SafeFlow MCP Server 导入失败: {e}')

try:
    from safeflow.adapters.semgrep_adapter import SemgrepAdapter
    print('✅ Semgrep 适配器导入成功')
except ImportError as e:
    print(f'❌ Semgrep 适配器导入失败: {e}')

try:
    from safeflow.adapters.syft_adapter import SyftAdapter
    print('✅ Syft 适配器导入成功')
except ImportError as e:
    print(f'❌ Syft 适配器导入失败: {e}')
"

# 步骤 8: 测试 MCP Server
echo ""
echo "🔧 步骤 8: 测试 MCP Server 启动"
echo "----------------------------------------"

echo "测试 MCP Server 启动（5秒超时）..."

# 创建测试输入
TEST_INPUT=$(mktemp)
cat > "$TEST_INPUT" << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"test","version":"1.0"}}}
EOF

# 测试启动
timeout 5s python -m safeflow.mcp.server < "$TEST_INPUT" > /tmp/mcp_test_output 2>&1 &
SERVER_PID=$!

sleep 2

if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ MCP Server 启动成功"
    kill $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
else
    echo "❌ MCP Server 启动失败"
    echo "错误输出:"
    cat /tmp/mcp_test_output
fi

# 清理
rm -f "$TEST_INPUT"
rm -f /tmp/mcp_test_output

# 步骤 9: 提供使用指南
echo ""
echo "🎉 设置完成！"
echo "========================================"
echo ""
echo "📚 使用指南:"
echo ""
echo "1. 激活虚拟环境:"
echo "   source venv/bin/activate"
echo ""
echo "2. 测试 MCP Server:"
echo "   python -m safeflow.mcp.server"
echo ""
echo "3. 运行演示脚本:"
echo "   python scripts/mcp_protocol_demo.py ./safeflow"
echo ""
echo "4. 运行交互式测试:"
echo "   python scripts/test_mcp_client.py"
echo ""
echo "5. 启动 HTTP 代理:"
echo "   python scripts/mcp_http_proxy.py"
echo ""
echo "6. 使用 MCP Inspector:"
echo "   bash scripts/start_mcp_inspector.sh"
echo ""
echo "💡 提示:"
echo "- 每次使用前都要激活虚拟环境: source venv/bin/activate"
echo "- 如果遇到导入错误，检查 PYTHONPATH 是否正确设置"
echo "- 查看 docs/MCP_TESTING_GUIDE.md 获取详细测试指南"
echo ""

# 保存激活命令到文件
cat > activate_safeflow.sh << 'EOF'
#!/bin/bash
# SafeFlow 虚拟环境激活脚本
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "✅ SafeFlow 环境已激活"
echo "   Python: $(which python)"
echo "   PYTHONPATH: $PYTHONPATH"
EOF

chmod +x activate_safeflow.sh

echo "📝 已创建快速激活脚本: ./activate_safeflow.sh"
echo "   使用方式: source ./activate_safeflow.sh"
echo ""

echo "🚀 现在可以开始使用 SafeFlow MCP 功能了！"
