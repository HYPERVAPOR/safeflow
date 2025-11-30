#!/bin/bash
# SafeFlow 安全工具安装脚本 - macOS 版本
#
# 包含各种回退机制和错误处理
# 支持多种安装方式和依赖检测

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检测 macOS 版本
detect_system() {
    log_info "检测 macOS 系统..."

    MAC_VERSION=$(sw_vers -productVersion)
    ARCH=$(uname -m)
    log_info "macOS 版本: $MAC_VERSION, 架构: $ARCH"

    # 检测 Homebrew
    if command -v brew &>/dev/null; then
        log_success "Homebrew 已安装: $(brew --version | head -1)"
        HOMEBREW_AVAILABLE=true
    else
        log_warning "Homebrew 未安装，将自动安装"
        HOMEBREW_AVAILABLE=false
    fi
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    if ! ping -c 1 google.com &>/dev/null && ! ping -c 1 apple.com &>/dev/null; then
        log_warning "网络连接可能有问题，某些下载可能失败"
        return 1
    fi
    log_success "网络连接正常"
    return 0
}

# 安装 Homebrew
install_homebrew() {
    if [[ "$HOMEBREW_AVAILABLE" == true ]]; then
        return 0
    fi

    log_info "安装 Homebrew..."
    if command -v /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        log_success "Homebrew 安装成功"

        # 添加到 PATH
        if [[ $ARCH == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        HOMEBREW_AVAILABLE=true
    else
        log_error "Homebrew 安装失败"
        return 1
    fi
}

# 安装 Xcode Command Line Tools
install_xcode_tools() {
    log_info "检查 Xcode Command Line Tools..."
    if ! xcode-select -p &>/dev/null; then
        log_info "安装 Xcode Command Line Tools..."
        xcode-select --install || {
            log_warning "Xcode 工具安装可能需要用户确认"
            log_info "请在弹出的对话框中点击'安装'"
        }
    else
        log_success "Xcode Command Line Tools 已安装"
    fi
}

# 安装基础依赖
install_base_dependencies() {
    log_info "安装基础依赖..."

    # 安装 Homebrew
    install_homebrew

    # 更新 Homebrew
    log_info "更新 Homebrew..."
    brew update || log_warning "Homebrew 更新失败"

    # 安装基础工具
    log_info "安装基础工具..."
    brew install curl wget git python3 || log_warning "部分工具安装失败"

    # Java (可选)
    if ! command -v java &>/dev/null; then
        log_info "安装 Java..."
        brew install openjdk@11 || brew install openjdk@17 || log_warning "Java 安装失败，OWASP ZAP 将无法使用"

        # 设置 JAVA_HOME
        if [[ -d "/opt/homebrew/opt/openjdk@11" ]]; then
            echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk@11"' >> ~/.zshrc
            echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.zshrc
        elif [[ -d "/opt/homebrew/opt/openjdk@17" ]]; then
            echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk@17"' >> ~/.zshrc
            echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.zshrc
        fi
    fi

    # 安装 Docker (可选)
    if ! command -v docker &>/dev/null; then
        log_info "安装 Docker Desktop..."
        brew install --cask docker || log_warning "Docker 安装失败，可作为回退方案"
    fi
}

# 创建用户目录
create_user_directories() {
    log_info "创建用户目录结构..."

    mkdir -p ~/bin
    mkdir -p ~/.local/bin
    mkdir -p ~/.safeflow/{tools,temp,results}

    # 确保 ~/bin 在 PATH 中
    if ! echo $PATH | grep -q "$HOME/bin"; then
        echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
        export PATH="$HOME/bin:$PATH"
        log_info "已将 ~/bin 添加到 PATH，请运行: source ~/.zshrc"
    fi

    log_success "用户目录创建完成"
}

# 安装 Semgrep
install_semgrep() {
    log_info "安装 Semgrep (静态代码分析工具)..."

    # 方法1: Homebrew (推荐)
    if [[ "$HOMEBREW_AVAILABLE" == true ]]; then
        log_info "方法1: 使用 Homebrew 安装..."
        if brew install semgrep; then
            log_success "Homebrew 安装成功"
            return 0
        else
            log_warning "Homebrew 安装失败，尝试其他方法"
        fi
    fi

    # 方法2: pip 安装 (回退)
    if command -v pip3 &>/dev/null; then
        log_info "方法2: 使用 pip 安装..."
        pip3 install --user semgrep || {
            log_warning "用户级安装失败，尝试虚拟环境..."
            python3 -m venv ~/.local/venv/semgrep
            ~/.local/venv/semgrep/bin/pip install semgrep
            ln -sf ~/.local/venv/semgrep/bin/semgrep ~/.local/bin/semgrep
        }
    fi

    # 方法3: 二进制下载 (回退)
    if ! command -v semgrep &>/dev/null; then
        log_info "方法3: 二进制下载 Semgrep..."
        SEGREP_VERSION=$(curl -s https://api.github.com/repos/returntocorp/semgrep/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
        if [[ -n "$SEGREP_VERSION" ]]; then
            case $ARCH in
                arm64) SEMGREP_ARCH="aarch64" ;;
                *) SEMGREP_ARCH="x86_64" ;;
            esac

            curl -L "https://github.com/returntocorp/semgrep/releases/download/${SEGREP_VERSION}/semgrep-v0-${SEMGREP_ARCH}-apple-darwin" -o ~/bin/semgrep
            chmod +x ~/bin/semgrep
        else
            log_error "Semgrep 下载失败"
            return 1
        fi
    fi

    # 验证安装
    if command -v semgrep &>/dev/null; then
        version=$(semgrep --version 2>/dev/null | head -1)
        log_success "Semgrep 安装成功: $version"
    else
        log_error "Semgrep 安装失败"
        return 1
    fi
}

# 安装 Trivy
install_trivy() {
    log_info "安装 Trivy (漏洞扫描工具)..."

    # 方法1: Homebrew (推荐)
    if [[ "$HOMEBREW_AVAILABLE" == true ]]; then
        log_info "方法1: 使用 Homebrew 安装..."
        if brew install trivy; then
            log_success "Homebrew 安装成功"
        else
            log_warning "Homebrew 安装失败，尝试其他方法"
        fi
    fi

    # 方法2: 二进制下载 (回退)
    if ! command -v trivy &>/dev/null; then
        log_info "方法2: 手动下载 Trivy..."
        TRIVY_VERSION=$(curl -s https://api.github.com/repos/aquasecurity/trivy/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
        if [[ -n "$TRIVY_VERSION" ]]; then
            case $ARCH in
                arm64) TRIVY_ARCH="arm64" ;;
                *) TRIVY_ARCH="amd64" ;;
            esac

            curl -L "https://github.com/aquasecurity/trivy/releases/download/${TRIVY_VERSION}/trivy_${TRIVY_VERSION#v}_macOS_${TRIVY_ARCH}.tar.gz" | tar -xz -C ~/bin trivy
            chmod +x ~/bin/trivy
        else
            log_error "Trivy 下载失败"
            return 1
        fi
    fi

    # 验证安装
    if command -v trivy &>/dev/null; then
        version=$(trivy --version | head -1)
        log_success "Trivy 安装成功: $version"

        # 更新漏洞数据库
        log_info "更新 Trivy 漏洞数据库..."
        trivy image --download-db || log_warning "数据库更新失败，将在首次扫描时自动更新"
    else
        log_error "Trivy 安装失败"
        return 1
    fi
}

# 安装 OWASP ZAP
install_zap() {
    log_info "安装 OWASP ZAP (Web 应用安全测试工具)..."

    # 检查 Java 环境
    if ! command -v java &>/dev/null; then
        log_warning "Java 未安装，跳过 OWASP ZAP 安装"
        log_info "建议运行: brew install openjdk@11"
        return 0
    fi

    # 方法1: Homebrew Cask (推荐)
    if [[ "$HOMEBREW_AVAILABLE" == true ]]; then
        log_info "方法1: 使用 Homebrew Cask 安装..."
        if brew install --cask owasp-zap; then
            log_success "Homebrew Cask 安装成功"
            return 0
        else
            log_warning "Homebrew Cask 安装失败，尝试其他方法"
        fi
    fi

    # 方法2: 直接下载 (回退)
    log_info "方法2: 直接下载 OWASP ZAP..."
    ZAP_VERSION=$(curl -s https://api.github.com/repos/zaproxy/zaproxy/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
    if [[ -n "$ZAP_VERSION" ]]; then
        ZAP_DIR="$HOME/bin/ZAP_${ZAP_VERSION}"
        curl -L "https://github.com/zaproxy/zaproxy/releases/download/${ZAP_VERSION}/ZAP_${ZAP_VERSION}_macOS.dmg" -o ~/Downloads/ZAP_${ZAP_VERSION}.dmg

        # 挂载 DMG 并复制应用
        if [[ -f ~/Downloads/ZAP_${ZAP_VERSION}.dmg ]]; then
            log_info "请手动挂载 DMG 文件并将 ZAP 应用复制到 Applications 文件夹"
            log_info "DMG 文件位置: ~/Downloads/ZAP_${ZAP_VERSION}.dmg"

            # 创建启动脚本
            cat > ~/bin/zap << 'EOF'
#!/bin/bash
if [[ -f "/Applications/ZAP.app/Contents/MacOS/zap.sh" ]]; then
    /Applications/ZAP.app/Contents/MacOS/zap.sh "$@"
else
    echo "请先安装 ZAP 应用程序"
    exit 1
fi
EOF
            chmod +x ~/bin/zap
        else
            log_error "ZAP 下载失败"
        fi
    fi

    # 方法3: Docker 安装 (回退)
    if ! command -v zap &>/dev/null && command -v docker &>/dev/null; then
        log_info "方法3: 使用 Docker 安装 OWASP ZAP..."
        docker pull owasp/zap2docker-stable || log_warning "Docker 安装失败"

        # 创建 Docker 脚本
        cat > ~/bin/zap-docker << 'EOF'
#!/bin/bash
docker run --rm -it -v "$(pwd):/zap/wrk" owasp/zap2docker-stable zap.sh "$@"
EOF
        chmod +x ~/bin/zap-docker
    fi

    # 验证安装
    if [[ -f "/Applications/ZAP.app/Contents/MacOS/zap.sh" ]] || command -v zap &>/dev/null || [[ -f ~/bin/zap-docker ]]; then
        log_success "OWASP ZAP 准备就绪"
        log_info "使用方法:"
        log_info "  - 应用程序: /Applications/ZAP.app"
        log_info "  - 命令行: ~/bin/zap"
        log_info "  - Docker: ~/bin/zap-docker"
    else
        log_error "OWASP ZAP 安装失败"
        return 1
    fi
}

# 安装 AFL++ (可选)
install_afl() {
    log_info "安装 AFL++ (模糊测试工具) [可选]..."

    # 检查 Xcode 工具
    if ! xcode-select -p &>/dev/null; then
        log_warning "Xcode Command Line Tools 未安装，跳过 AFL++ 安装"
        return 0
    fi

    # 方法1: Homebrew (推荐)
    if [[ "$HOMEBREW_AVAILABLE" == true ]]; then
        log_info "方法1: 使用 Homebrew 安装..."
        if brew install afl-fuzz; then
            log_success "Homebrew 安装成功"
            return 0
        else
            log_warning "Homebrew 安装失败，尝试源码编译"
        fi
    fi

    # 方法2: 源码编译 (回退)
    log_info "方法2: 从源码编译 AFL++..."
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    if git clone https://github.com/AFLplusplus/AFLplusplus.git; then
        cd AFLplusplus
        make all || log_warning "编译失败"

        # 安装到用户目录
        mkdir -p ~/bin/afl
        cp afl-* ~/bin/afl/ 2>/dev/null || true

        # 创建符号链接
        ln -sf ~/bin/afl/afl-fuzz ~/bin/afl-fuzz
        ln -sf ~/bin/afl/afl-gcc ~/bin/afl-gcc
    fi

    cd ~
    rm -rf "$TEMP_DIR"

    # 验证安装
    if command -v afl-fuzz &>/dev/null || [[ -f ~/bin/afl-fuzz ]]; then
        log_success "AFL++ 安装成功"
    else
        log_warning "AFL++ 安装失败（可选工具，不影响主要功能）"
    fi
}

# 创建验证脚本
create_verification_script() {
    log_info "创建验证脚本..."

    cat > ~/.safeflow/verify-installation.sh << 'EOF'
#!/bin/bash
# SafeFlow 工具验证脚本

export PATH="$HOME/bin:$HOME/.local/bin:$PATH"

total=0
passed=0

echo "🔍 SafeFlow 工具安装验证 (macOS)"
echo "================================="

verify() {
    local name=$1
    local cmd=$2
    ((total++))
    echo -n "验证 $name ... "

    if eval "$cmd" &>/dev/null; then
        echo "✅ 通过"
        ((passed++))
    else
        echo "❌ 失败"
    fi
}

echo 'import os; os.system("echo test")' > /tmp/test_vuln.py

verify "Semgrep" "command -v semgrep"
verify "Trivy" "command -v trivy"
verify "OWASP ZAP" "test -f /Applications/ZAP.app/Contents/MacOS/zap.sh"
verify "Java 环境" "command -v java"
verify "Homebrew" "command -v brew"
verify "Docker" "command -v docker"

rm -f /tmp/test_vuln.py

echo ""
echo "📊 验证结果: $passed/$total 通过"
echo ""
echo "工具版本信息:"
command -v semgrep &>/dev/null && echo "  Semgrep: $(semgrep --version | head -1)"
command -v trivy &>/dev/null && echo "  Trivy: $(trivy --version | head -1)"
command -v java &>/dev/null && echo "  Java: $(java -version 2>&1 | head -1)"
command -v brew &>/dev/null && echo "  Homebrew: $(brew --version | head -1)"

if [[ -f "/Applications/ZAP.app/Contents/MacOS/zap.sh" ]]; then
    echo "  OWASP ZAP: $(/Applications/ZAP.app/Contents/MacOS/zap.sh -version 2>&1 | head -1 || echo "已安装")"
fi
EOF

    chmod +x ~/.safeflow/verify-installation.sh
    log_success "验证脚本已创建: ~/.safeflow/verify-installation.sh"
}

# 主安装流程
main() {
    echo "🚀 SafeFlow 安全工具安装脚本 - macOS 版本"
    echo "============================================"
    echo ""

    # 检测系统
    detect_system

    # 检查网络
    check_network || log_warning "网络问题可能影响下载"

    # 安装 Xcode 工具
    install_xcode_tools

    # 创建目录
    create_user_directories

    # 安装基础依赖
    install_base_dependencies

    # 安装各个工具
    echo ""
    log_info "开始安装安全工具..."

    if install_semgrep; then
        log_success "Semgrep 安装完成"
    else
        log_error "Semgrep 安装失败"
    fi

    if install_trivy; then
        log_success "Trivy 安装完成"
    else
        log_error "Trivy 安装失败"
    fi

    if install_zap; then
        log_success "OWASP ZAP 准备完成"
    else
        log_warning "OWASP ZAP 安装失败"
    fi

    # AFL++ 是可选的
    echo ""
    log_info "安装可选工具 AFL++ (模糊测试)..."
    install_afl

    # 创建验证脚本
    create_verification_script

    echo ""
    echo "🎉 安装脚本执行完成！"
    echo ""
    echo "📋 后续步骤:"
    echo "  1. 重新加载环境: source ~/.zshrc"
    echo "  2. 运行验证脚本: ~/.safeflow/verify-installation.sh"
    echo "  3. 查看安装指南: /home/hv/projs/safeflow/docs/tool-installation-guide.md"
    echo ""
    echo "⚠️  macOS 特别注意事项:"
    echo "  - 首次使用某些工具需要授权安全访问权限"
    echo "  - OWASP ZAP 可能需要手动挂载 DMG 文件"
    echo "  - 某些工具在首次运行时需要下载依赖"
    echo "  - 防火墙可能需要允许网络连接"
}

# 运行主程序
main "$@"