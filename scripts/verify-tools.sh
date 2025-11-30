#!/bin/bash
# SafeFlow 工具验证脚本

# 设置 PATH
export PATH="$HOME/bin:$PATH"

# 计数器
total=0
passed=0

echo "🔍 SafeFlow 安全工具验证"
echo "============================="

# 验证函数
verify() {
    local name=$1
    local cmd=$2

    ((total++))
    echo -n "检查 $name ... "

    if eval "$cmd" &>/dev/null; then
        echo "✅ 通过"
        ((passed++))
    else
        echo "❌ 失败"
    fi
}

# 创建测试文件
echo 'import os; os.system("echo test")' > /tmp/test_vuln.py

# 执行验证
verify "Semgrep 安装" "command -v semgrep"
verify "Semgrep 功能" "semgrep --config=auto /tmp/test_vuln.py"
verify "Trivy 安装" "command -v trivy"
verify "Trivy 功能" "trivy fs /tmp/test_vuln.py"
verify "OWASP ZAP 文件" "test -f $HOME/bin/ZAP_2.16.1/zap-2.16.1.jar"

# 清理
rm -f /tmp/test_vuln.py

# 结果
echo ""
echo "📊 验证结果: $passed/$total 通过"

success_rate=$((passed * 100 / total))

if [[ $success_rate -eq 100 ]]; then
    echo "🎉 所有工具验证通过！SafeFlow 环境准备就绪。"
    exit 0
elif [[ $success_rate -ge 80 ]]; then
    echo "⚠️  大部分工具验证通过，请检查失败的工具。"
    exit 0
else
    echo "❌ 多个工具验证失败，请重新安装配置。"
    exit 1
fi