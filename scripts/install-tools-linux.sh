#!/bin/bash
# SafeFlow 安全工具安装脚本 - Linux 版本
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

# 系统信息
DISTRO=""
PACKAGE_MANAGER=""

# 检测系统信息
detect_system() {
    log_info "检测系统信息..."

    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif command -v lsb_release &>/dev/null; then
        DISTRO=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
    else
        DISTRO="unknown"
    fi

    # 检测包管理器
    if command -v apt &>/dev/null; then
        PACKAGE_MANAGER="apt"
    elif command -v yum &>/dev/null; then
        PACKAGE_MANAGER="yum"
    elif command -v dnf &>/dev/null; then
        PACKAGE_MANAGER="dnf"
    elif command -v pacman &>/dev/null; then
        PACKAGE_MANAGER="pacman"
    elif command -v zypper &>/dev/null; then
        PACKAGE_MANAGER="zypper"
    else
        log_warning "未识别的包管理器"
        PACKAGE_MANAGER="unknown"
    fi

    log_info "系统: $DISTRO, 包管理器: $PACKAGE_MANAGER"
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    if ! ping -c 1 google.com &>/dev/null && ! ping -c 1 baidu.com &>/dev/null; then
        log_warning "网络连接可能有问题，某些下载可能失败"
        return 1
    fi
    log_success "网络连接正常"
    return 0
}

# 安装基础依赖
install_base_dependencies() {
    log_info "安装基础依赖..."

    case $PACKAGE_MANAGER in
        apt)
            # 更新包列表
            sudo apt update

            # 安装基础工具
            sudo apt install -y curl wget git unzip python3 python3-pip python3-venv build-essential

            # Java (可选)
            if ! command -v java &>/dev/null; then
                log_warning "Java 未安装，尝试安装 OpenJDK 11..."
                sudo apt install -y openjdk-11-jdk || {
                    log_warning "Java 11 安装失败，尝试 Java 17..."
                    sudo apt install -y openjdk-17-jdk || log_warning "Java 安装失败，OWASP ZAP 将无法使用"
                }
            fi
            ;;

        yum|dnf)
            sudo $PACKAGE_MANAGER update -y
            sudo $PACKAGE_MANAGER install -y curl wget git unzip python3 python3-pip python3-devel gcc gcc-c++ make

            if ! command -v java &>/dev/null; then
                log_warning "Java 未安装，尝试安装 OpenJDK..."
                sudo $PACKAGE_MANAGER install -y java-11-openjdk || sudo $PACKAGE_MANAGER install -y java-17-openjdk || log_warning "Java 安装失败"
            fi
            ;;

        pacman)
            sudo pacman -Sy --noconfirm
            sudo pacman -S --noconfirm curl wget git unzip python python-pip base-devel jdk11-openjdk || sudo pacman -S --noconfirm jdk17-openjdk || log_warning "Java 安装失败"
            ;;

        zypper)
            sudo zypper refresh
            sudo zypper install -y curl wget git unzip python3 python3-pip gcc gcc-c++ make java-11-openjdk || log_warning "部分依赖安装失败"
            ;;

        *)
            log_warning "未知包管理器，请手动安装基础依赖: curl, wget, git, python3, pip"
            ;;
    esac
}

# 创建用户目录
create_user_directories() {
    log_info "创建用户目录结构..."

    mkdir -p ~/bin
    mkdir -p ~/.local/bin
    mkdir -p ~/.safeflow/{tools,temp,results}

    # 确保 ~/bin 在 PATH 中
    if ! echo $PATH | grep -q "$HOME/bin"; then
        echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/bin:$PATH"
        log_info "已将 ~/bin 添加到 PATH，请运行: source ~/.bashrc"
    fi

    # 确保 ~/.local/bin 在 PATH 中
    if ! echo $PATH | grep -q "$HOME/.local/bin"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi

    log_success "用户目录创建完成"
}

# 安装 Semgrep
install_semgrep() {
    log_info "安装 Semgrep (静态代码分析工具)..."

    # 方法1: 使用 pip (推荐)
    if command -v pip3 &>/dev/null; then
        log_info "方法1: 使用 pip 安装 Semgrep..."
        pip3 install --user semgrep || {
            log_warning "用户级安装失败，尝试系统级安装..."
            sudo pip3 install semgrep || {
                log_warning "系统级 pip 安装失败，尝试虚拟环境..."
                python3 -m venv ~/.local/venv/semgrep
                ~/.local/venv/semgrep/bin/pip install semgrep
                ln -sf ~/.local/venv/semgrep/bin/semgrep ~/.local/bin/semgrep
            }
        }
    fi

    # 方法2: 二进制安装 (回退)
    if ! command -v semgrep &>/dev/null; then
        log_info "方法2: 二进制安装 Semgrep..."
        SEGREP_VERSION=$(curl -s https://api.github.com/repos/returntocorp/semgrep/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
        if [[ -n "$SEGREP_VERSION" ]]; then
            curl -L "https://github.com/returntocorp/semgrep/releases/download/${SEGREP_VERSION}/semgrep-v0-linux" -o ~/bin/semgrep
            chmod +x ~/bin/semgrep
        else
            log_error "Semgrep 二进制下载失败"
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

    # 方法1: 官方安装脚本 (推荐)
    log_info "方法1: 使用官方安装脚本..."
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b ~/bin || {
        log_warning "官方脚本安装失败，尝试手动下载..."

        # 方法2: 手动下载 (回退)
        log_info "方法2: 手动下载 Trivy..."
        TRIVY_VERSION=$(curl -s https://api.github.com/repos/aquasecurity/trivy/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
        if [[ -n "$TRIVY_VERSION" ]]; then
            ARCH=$(uname -m)
            case $ARCH in
                x86_64) TRIVY_ARCH="amd64" ;;
                aarch64|arm64) TRIVY_ARCH="arm64" ;;
                *) TRIVY_ARCH="386" ;;
            esac

            curl -L "https://github.com/aquasecurity/trivy/releases/download/${TRIVY_VERSION}/trivy_${TRIVY_VERSION#v}_Linux_${TRIVY_ARCH}.tar.gz" | tar -xz -C ~/bin trivy
            chmod +x ~/bin/trivy
        else
            log_error "Trivy 下载失败"
            return 1
        fi
    }

    # 方法3: 包管理器安装 (回退)
    if ! command -v trivy &>/dev/null; then
        log_info "方法3: 使用包管理器安装..."
        case $PACKAGE_MANAGER in
            apt)
                curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
                echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
                sudo apt update
                sudo apt install -y trivy || log_warning "包管理器安装失败"
                ;;
            *)
                log_warning "当前包管理器不支持 Trivy，请使用手动安装"
                ;;
        esac
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
        log_info "建议安装 Java 11+ 以使用 OWASP ZAP"
        return 0
    fi

    # 检查 Java 版本
    JAVA_VERSION=$(java -version 2>&1 | head -1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
    if [[ -n "$JAVA_VERSION" ]]; then
        if [[ $(echo "$JAVA_VERSION < 1.8" | bc -l 2>/dev/null || echo "0") == "1" ]]; then
            log_warning "Java 版本过低 ($JAVA_VERSION)，OWASP ZAP 需要 Java 8+"
            return 0
        fi
    fi

    # 方法1: 直接下载 (推荐)
    log_info "方法1: 直接下载 OWASP ZAP..."
    ZAP_VERSION=$(curl -s https://api.github.com/repos/zaproxy/zaproxy/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
    if [[ -n "$ZAP_VERSION" ]]; then
        ZAP_DIR="$HOME/bin/ZAP_${ZAP_VERSION}"
        curl -L "https://github.com/zaproxy/zaproxy/releases/download/${ZAP_VERSION}/ZAP_${ZAP_VERSION}_Linux.tar.gz" | tar -xz -C ~/bin

        if [[ -d "$ZAP_DIR" ]]; then
            ln -sf "$ZAP_DIR/zap.sh" ~/bin/zap
            chmod +x "$ZAP_DIR/zap.sh"
            log_success "OWASP ZAP 下载完成: $ZAP_VERSION"
        else
            log_warning "下载解压失败，尝试包管理器安装"
        fi
    fi

    # 方法2: 包管理器安装 (回退)
    if ! [[ -d "$HOME/bin/ZAP_"* ]]; then
        log_info "方法2: 使用包管理器安装..."
        case $PACKAGE_MANAGER in
            apt)
                sudo apt install -y zaproxy || log_warning "包管理器安装失败"
                ;;
            *)
                log_warning "当前包管理器不支持 OWASP ZAP"
                ;;
        esac
    fi

    # 方法3: Docker 安装 (回退)
    if ! [[ -d "$HOME/bin/ZAP_"* ]] && ! command -v zap &>/dev/null; then
        if command -v docker &>/dev/null; then
            log_info "方法3: 使用 Docker 安装 OWASP ZAP..."
            docker pull owasp/zap2docker-stable || log_warning "Docker 安装失败"

            # 创建 Docker 脚本
            cat > ~/bin/zap-docker << 'EOF'
#!/bin/bash
docker run --rm -it -v "$(pwd):/zap/wrk" owasp/zap2docker-stable zap.sh "$@"
EOF
            chmod +x ~/bin/zap-docker
        else
            log_warning "Docker 未安装，无法使用 Docker 方式"
        fi
    fi

    # 验证安装
    if [[ -d "$HOME/bin/ZAP_"* ]] || command -v zap &>/dev/null || [[ -f ~/bin/zap-docker ]]; then
        log_success "OWASP ZAP 准备就绪"
        log_info "使用方法:"
        log_info "  - 本地安装: ~/bin/ZAP_*/zap.sh"
        log_info "  - Docker: ~/bin/zap-docker"
    else
        log_error "OWASP ZAP 安装失败"
        return 1
    fi
}

# 安装 AFL++ (可选)
install_afl() {
    log_info "安装 AFL++ (模糊测试工具) [可选]..."

    # 检查编译环境
    if ! command -v gcc &>/dev/null; then
        log_warning "GCC 未安装，跳过 AFL++ 安装"
        return 0
    fi

    # 方法1: 包管理器安装 (推荐)
    case $PACKAGE_MANAGER in
        apt)
            sudo apt install -y afl++ afl-quick || log_warning "包管理器安装失败"
            ;;
        pacman)
            sudo pacman -S --noconfirm afl || log_warning "包管理器安装失败"
            ;;
        *)
            log_warning "当前包管理器不支持 AFL++"
            ;;
    esac

    # 方法2: 源码编译 (回退)
    if ! command -v afl-fuzz &>/dev/null; then
        log_info "方法2: 从源码编译 AFL++..."
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"

        if git clone https://github.com/AFLplusplus/AFLplusplus.git; then
            cd AFLplusplus
            make all || log_warning "编译失败"
            sudo make install || log_warning "安装失败"
        fi

        cd ~
        rm -rf "$TEMP_DIR"
    fi

    # 验证安装
    if command -v afl-fuzz &>/dev/null; then
        version=$(afl-fuzz --version 2>/dev/null || echo "未知版本")
        log_success "AFL++ 安装成功: $version"
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

echo "🔍 SafeFlow 工具安装验证"
echo "==============================="

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
verify "OWASP ZAP" "test -f ~/bin/ZAP_*/zap-*.jar"
verify "Java 环境" "command -v java"
verify "Docker 环境" "command -v docker"

rm -f /tmp/test_vuln.py

echo ""
echo "📊 验证结果: $passed/$total 通过"
echo ""
echo "工具版本信息:"
command -v semgrep &>/dev/null && echo "  Semgrep: $(semgrep --version | head -1)"
command -v trivy &>/dev/null && echo "  Trivy: $(trivy --version | head -1)"
command -v java &>/dev/null && echo "  Java: $(java -version 2>&1 | head -1)"

if [[ -d "$HOME/bin/ZAP_"* ]]; then
    echo "  OWASP ZAP: $(ls -d $HOME/bin/ZAP_* | sed 's/.*\///')"
fi
EOF

    chmod +x ~/.safeflow/verify-installation.sh
    log_success "验证脚本已创建: ~/.safeflow/verify-installation.sh"
}

# 主安装流程
main() {
    echo "🚀 SafeFlow 安全工具安装脚本 - Linux 版本"
    echo "============================================="
    echo ""

    # 检查权限
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用 root 用户运行此脚本"
        exit 1
    fi

    # 检测系统
    detect_system

    # 检查网络
    check_network || log_warning "网络问题可能影响下载"

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
    echo "  1. 重新加载环境: source ~/.bashrc"
    echo "  2. 运行验证脚本: ~/.safeflow/verify-installation.sh"
    echo "  3. 查看安装指南: /home/hv/projs/safeflow/docs/tool-installation-guide.md"
    echo ""
    echo "⚠️  注意事项:"
    echo "  - 某些工具需要额外配置（如 Java 环境）"
    echo "  - 防火墙可能需要配置允许网络访问"
    echo "  - 首次运行时某些工具会自动下载数据库"
}

# 运行主程序
main "$@"