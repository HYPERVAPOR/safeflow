# SafeFlow 安全工具安装指南

本文档提供 SafeFlow 平台中各种安全测试工具的详细安装指南，包括静态分析、动态分析、依赖分析和模糊测试工具。

## 📋 目录

- [环境要求](#环境要求)
- [快速安装](#快速安装)
- [详细安装指南](#详细安装指南)
  - [Semgrep (静态分析工具)](#semgrep-静态分析工具)
  - [Trivy (漏洞扫描工具)](#trivy-漏洞扫描工具)
  - [OWASP ZAP (Web 应用安全测试)](#owasp-zap-web-应用安全测试)
  - [AFL++ (模糊测试工具)](#afl-模糊测试工具)
- [工具测试和验证](#工具测试和验证)
- [常见问题](#常见问题)
- [集成到 SafeFlow](#集成到-safeflow)

## 🔧 环境要求

### 基础要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+), macOS, 或 Windows (WSL2)
- **Python**: 3.8+ (推荐 3.11+)
- **Git**: 版本控制工具
- **基础网络**: 用于下载工具和更新数据库

### 可选要求
- **Docker**: 用于容器化部署和工具隔离
- **Java 11+**: 用于运行 OWASP ZAP (Web 安全测试)
- **GCC**: 用于编译 AFL++ (模糊测试)

### 系统检查

```bash
# 检查 Python 版本
python3 --version

# 检查 Git
git --version

# 检查 Docker (可选)
docker --version

# 检查 Java (可选)
java --version
```

## ⚡ 快速安装

### 一键安装脚本

```bash
#!/bin/bash
# SafeFlow 安全工具快速安装脚本

set -e

echo "🔧 开始安装 SafeFlow 安全工具..."

# 1. 安装 Semgrep (静态分析)
echo "📊 安装 Semgrep..."
pip3 install semgrep

# 2. 安装 Trivy (漏洞扫描)
echo "🛡️ 安装 Trivy..."
mkdir -p ~/bin
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b ~/bin

# 3. 下载 OWASP ZAP (需要 Java)
echo "🕷️ 下载 OWASP ZAP..."
ZAP_VERSION=$(curl -s https://api.github.com/repos/zaproxy/zaproxy/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
curl -fsSL https://github.com/zaproxy/zaproxy/releases/download/${ZAP_VERSION}/ZAP_${ZAP_VERSION}_Linux.tar.gz | tar -xz -C ~/bin

# 4. 设置环境变量
echo "⚙️ 设置环境变量..."
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc

echo "✅ 安装完成！请重新加载 shell 或运行 source ~/.bashrc"
```

### 使用快速安装

```bash
# 下载并运行安装脚本
curl -fsSL https://raw.githubusercontent.com/your-repo/safeflow/main/docs/install-tools.sh | bash

# 或者直接下载脚本后运行
wget https://raw.githubusercontent.com/your-repo/safeflow/main/docs/install-tools.sh
chmod +x install-tools.sh
./install-tools.sh
```

## 📖 详细安装指南

### 🔍 Semgrep (静态分析工具)

#### 简介
Semgrep 是一个快速、可定制的静态分析工具，用于在代码中发现漏洞和安全问题。

#### 安装方法

**方法 1: 使用 pip (推荐)**
```bash
pip3 install semgrep
```

**方法 2: 使用 conda**
```bash
conda install -c conda-forge semgrep
```

**方法 3: 从源码安装**
```bash
git clone https://github.com/returntocorp/semgrep
cd semgrep
pip3 install -e .
```

#### 验证安装

```bash
semgrep --version
# 输出示例: 1.144.0

# 基本功能测试
semgrep --help

# 测试扫描
echo 'os.system("rm -rf /")' > test.py
semgrep --config=auto test.py
```

#### 配置文件

创建 `~/.semgrepconfig`:
```yaml
# ~/.semgrepconfig
rules:
  - id: security.semgrep.dev
    languages: [python, javascript, typescript]
    pattern-either:
      - os.system: |
          os.system(...)
      - exec: |
          exec(...)
      - subprocess: |
          subprocess.Popen(...)

metrics:
  - debug
  - find-sinks
  - tests
```

#### 常用命令

```bash
# 基础扫描
semgrep --config=auto /path/to/code

# 自定义规则扫描
semgrep --config=my-rules.yml /path/to/code

# JSON 输出
semgrep --config=auto --json --output=results.json /path/to/code

# 调试模式
semgrep --config=auto --debug /path/to/code
```

### 🛡️ Trivy (漏洞扫描工具)

#### 简介
Trivy 是一个简单而全面的安全扫描器，支持容器、文件系统和 Git 仓库的漏洞扫描。

#### 安装方法

**方法 1: 二进制安装 (推荐)**
```bash
mkdir -p ~/bin
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b ~/bin
```

**方法 2: 包管理器安装**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# macOS
brew install trivy

# Windows (使用 Chocolatey)
choco install trivy
```

**方法 3: Docker 安装**
```bash
docker pull aquasec/trivy:latest
docker run --rm aquasec/trivy --help
```

#### 验证安装

```bash
# 确保 PATH 包含 ~/bin
export PATH="$HOME/bin:$PATH"

trivy --version
# 输出示例: Version: 0.67.2

# 更新漏洞数据库
trivy image --download-db

# 基础测试
trivy --help
```

#### 配置文件

创建 `~/.trivy.yaml`:
```yaml
# ~/.trivy.yaml
format: "json"
severity: ["CRITICAL", "HIGH", "MEDIUM"]

# 忽略的漏洞
ignore-unfixed: true

# 自定义规则
custom-rules:
  - name: "example rule"
    language: "dockerfile"
    type: "regex"
    pattern: "ADD http://.*\\.com"
    message: "Add HTTP endpoint is not recommended"

# 扫描配置
scan:
  skip-dirs:
    - "vendor"
    - "node_modules"
    - ".git"
```

#### 常用命令

```bash
# 扫描文件系统
trivy fs /path/to/project

# 扫描容器镜像
trivy image nginx:latest

# 扫描 Git 仓库
trivy repo https://github.com/example/repo

# JSON 输出
trivy fs --format json --output=results.json /path/to/project

# 详细扫描
trivy fs --severity CRITICAL,HIGH,MEDIUM /path/to/project
```

### 🕷️ OWASP ZAP (Web 应用安全测试)

#### 简介
OWASP ZAP (Zed Attack Proxy) 是一个开源的 Web 应用安全测试工具，用于自动发现 Web 应用中的安全漏洞。

#### 系统要求

- Java 11 或更高版本
- 足够的内存 (建议 2GB+)

#### 安装方法

**方法 1: 二进制下载 (推荐)**
```bash
# 获取最新版本
ZAP_VERSION=$(curl -s https://api.github.com/repos/zaproxy/zaproxy/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)

# 下载并解压
curl -fsSL https://github.com/zaproxy/zaproxy/releases/download/${ZAP_VERSION}/ZAP_${ZAP_VERSION}_Linux.tar.gz | tar -xz -C ~/bin

# 创建符号链接
ln -sf ~/bin/ZAP_${ZAP_VERSION}/zap.sh ~/bin/zap
```

**方法 2: 包管理器安装**
```bash
# Ubuntu/Debian
sudo apt-get install zaproxy

# macOS
brew install --cask owasp-zap

# Windows
# 下载 .exe 安装包并运行
```

**方法 3: Docker 安装**
```bash
# 官器化部署
docker pull owasp/zap2docker-stable

# 运行 ZAP
docker run -t owasp/zap2docker-stable zap.sh -cmd quickstart
```

#### 验证安装

```bash
# 检查 Java
java -version

# 启动 ZAP (后台模式)
java -jar ~/bin/ZAP_2.16.1/zap.sh -daemon -port 8080 -host 0.0.0.0

# 使用 ZAP CLI
curl -s "http://localhost:8080/JSON/core/view/version/" | jq .

# 停止 ZAP
curl -s "http://localhost:8080/JSON/core/action/shutdown/"
```

#### 配置选项

```bash
# 命令行参数
java -jar ~/bin/ZAP_2.16.1/zap.sh \
  -config api.addrs.addr.name=0.0.0.0 \
  -config api.addrs.addr.port=8080 \
  -config scanner.strength=INSIGHT \
  -daemon

# API 配置
# http://localhost:8080/JSON/core/view/optionDefaultAttackStrength/
curl -X PUT http://localhost:8080/JSON/core/setOptionDefaultAttackStrength \
  -H "Content-Type: application/json" \
  -d '{"Strength": "HIGH"}'
```

#### 常用命令

```bash
# 快速扫描
java -jar ~/bin/ZAP_2.16.1/zap.sh -quickstart -cmd quickscan -t http://example.com

# 被动扫描
java -jar ~/bin/ZAP_2.16.1/zap.sh -cmd zaproxy -t http://example.com

# API 扫描
java -jar ~/bin/ZAP_2.16.1/zap.sh -cmd apitest -t http://example.com/api

# 导出报告
curl -s "http://localhost:8080/JSON/core/view/optionDefaultReportAuthor/" | jq .
```

### 🔄 AFL++ (模糊测试工具)

#### 简介
AFL++ (American Fuzzy Lop plus plus) 是一个先进的、覆盖率导向的模糊测试工具，用于发现软件中的安全漏洞。

#### 系统要求

- GCC 或 Clang 编译器
- 开发工具包 (build-essential)
- Linux 内核支持 (可选)

#### 安装方法

**方法 1: 从源码编译 (推荐)**
```bash
# 安装依赖
sudo apt-get update
sudo apt-get install build-essential git libdisasm-dev

# 克隆源码
git clone https://github.com/AFLplusplus/AFLplusplus.git
cd AFLplusplus

# 编译安装
make all
sudo make install

# 安装 afl-quick
sudo apt-get install afl-quick
```

**方法 2: 包管理器安装**
```bash
# Ubuntu/Debian
sudo apt-get install afl++

# macOS
brew install afl-fuzz

# Arch Linux
sudo pacman -S afl
```

**方法 3: Docker 安装**
```bash
# 使用预编译的 Docker 镜像
docker pull aflplusplus/aflplusplus
```

#### 验证安装

```bash
afl-fuzz --version
# 输出示例: afl-fuzz++ 4.25c (Ubuntu 24.04)

# 创建测试程序
echo 'int main(int argc, char **argv) { return argv[argc-1][0]; }' > test.c
gcc -g -o test test.c

# 基础模糊测试
mkdir -p in out
echo "test" > in/test.txt
afl-fuzz -i in -o out ./test
```

#### 配置选项

```bash
# 设置环境变量
export AFL_SKIP_CPUFREQ=1
export AFL_I_DONT_CARE_1_MIN=25

# 创建 afl-quick 配置
cat > afl-quick.conf << 'EOF'
 afl-quick -c -i in -o out -- ./test
EOF

# 使用 QEMU 模式 (二进制模糊测试)
afl-fuzz -Q -i in -o out -- ./target_binary
```

#### 常用命令

```bash
# 基础模糊测试
afl-fuzz -i input_dir -o output_dir ./target_program

# 多核心并行模糊测试
afl-fuzz -i input_dir -o output_dir -M -m ./target_program

# 网络模糊测试
afl-fuzz -i input_dir -o output_dir -N tcp://127.0.0.1:8080

# QEMU 模式 (闭源软件)
afl-fuzz -Q -i input_dir -o output_dir ./target_binary

# AFL-quick 快速测试
afl-quick -i input_dir -o output_dir ./target_program
```

## ✅ 工具测试和验证

### 测试项目创建

创建一个简单的测试项目来验证工具功能：

```bash
# 创建测试目录
mkdir -p ~/safeflow-test
cd ~/safeflow-test

# 创建有问题的 Python 代码
cat > insecure_app.py << 'EOF
import os
import subprocess

def process_user_input(user_data):
    # 安全问题: 直接使用用户输入
    os.system(f"echo {user_data}")

    # 安全问题: 命令注入
    subprocess.Popen(user_data, shell=True)

    return "Processed"

def get_database_config():
    # 安全问题: 硬编码密码
    password = "admin123"
    connection_string = f"mysql://user:{password}@localhost/db"
    return connection_string

# 安全问题: 路径遍历
def read_file(filename):
    with open(f"/tmp/{filename}", "r") as f:
        return f.read()

if __name__ == "__main__":
    user_input = input("Enter data: ")
    process_user_input(user_input)
EOF

# 创建简单的 HTML 页面
cat > index.html << 'EOF
<!DOCTYPE html>
<html>
<head>
    <title>Test Application</title>
</head>
<body>
    <h1>Welcome</h1>
    <form action="/submit" method="POST">
        <input type="text" name="user_input" />
        <input type="submit" value="Submit" />
    </form>
</body>
</html>
EOF

# 创建 Dockerfile
cat > Dockerfile << 'EOF
FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
EOF

# 创建 requirements.txt
cat > requirements.txt << 'EOF
flask==2.3.3
EOF
```

### 运行测试

```bash
# 1. Semgrep 测试
echo "🔍 测试 Semgrep..."
semgrep --config=auto --json --output=semgrep_results.json insecure_app.py

# 2. Trivy 测试
echo "🛡️ 测试 Trivy..."
trivy fs --format json --output=trivy_results.json .

# 3. 创建简单的 Web 应用进行 ZAP 测试
cat > app.py << 'EOF
from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to SafeFlow Test App"

@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form.get('user_input', '')
    # 这里添加了一些不安全的功能
    return f"Processed: {user_input}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# 启动测试应用 (后台)
python3 app.py &
APP_PID=$!

# 4. 等待应用启动，然后进行 ZAP 测试
echo "🕷️ 测试 OWASP ZAP..."
sleep 5

# 5. 清理
kill $APP_PID 2>/dev/null || true
```

### 结果检查

```bash
# 检查结果文件
echo "📊 检查扫描结果..."
ls -la *_results.json

# 显示 Semgrep 结果摘要
if [ -f semgrep_results.json ]; then
    echo "Semgrep 发现的问题:"
    jq '.results | length' semgrep_results.json
fi

# 显示 Trivy 结果摘要
if [ -f trivy_results.json ]; then
    echo "Trivy 发现的漏洞:"
    jq '.Results | length' trivy_results.json
fi
```

## ❓ 常见问题

### Semgrep 问题

**Q: Semgrep 安装失败**
```bash
# 解决方案: 使用虚拟环境
python3 -m venv semgrep-env
source semgrep-env/bin/activate
pip install semgrep
```

**Q: 规则不生效**
```bash
# 检查规则路径
semgrep --list-configs
# 使用绝对路径
semgrep --config=/path/to/rules.yml
```

### Trivy 问题

**Q: 数据库更新失败**
```bash
# 解决方案: 使用代理
export TRIVY_TEMP_DIR=/tmp/trivy
trivy image --download-db --cache-dir $TRIVY_TEMP_DIR
```

**Q: 权限不足**
```bash
# 解决方案: 使用用户目录
mkdir -p ~/.trivy
chmod 755 ~/.trivy
```

### OWASP ZAP 问题

**Q: Java 版本不兼容**
```bash
# 检查 Java 版本
java -version

# 安装 Java 11
sudo apt-get update
sudo apt-get install openjdk-11-jdk
```

**Q: 内存不足**
```bash
# 增加 Java 内存
java -Xmx4g -jar ~/bin/ZAP_2.16.1/zap.sh
```

### AFL++ 问题

**Q: 编译错误**
```bash
# 安装编译依赖
sudo apt-get install build-essential

# 检查内核支持
grep CONFIG_PERF_EVENTS /boot/config-*.config
```

**Q: 需要特殊权限**
```bash
# 设置 core 模式
echo core | sudo tee /proc/sys/kernel/core_pattern
sudo sysctl -w kernel.core_pattern=core.%p
```

## 🔗 集成到 SafeFlow

### 工具配置文件

创建工具配置目录和文件：

```bash
# 创建配置目录
mkdir -p ~/.safeflow/tools

# 创建 Semgrep 配置
cat > ~/.safeflow/tools/semgrep.yaml << 'EOF
# SafeFlow Semgrep 配置
config:
  severity: ["ERROR", "WARNING"]
  json: true
  output: "semgrep_results.json"

rules:
  - security.semgrep.dev
  - owasp-top-ten
  - path-traversal
  - sql-injection

metrics:
  - debug
  - tests
EOF

# 创建 Trivy 配置
cat > ~/.safeflow/tools/trivy.yaml << 'EOF
# SafeFlow Trivy 配置
format: "json"
output: "trivy_results.json"
severity: ["CRITICAL", "HIGH", "MEDIUM"]
ignore-unfixed: true

scan:
  skip-dirs:
    - "vendor"
    - "node_modules"
    - ".git"
  skip-files:
    - "*.test.js"
    - "*.spec.ts"

db:
  type: "sqlite"
  path: "~/.trivy/db/trivy.db"
EOF

# 创建 ZAP 配置
cat > ~/.safeflow/tools/zap.properties << 'EOF
# SafeFlow ZAP 配置
api.addrs.addr.name=0.0.0.0
api.addrs.addr.port=8080
scanner.strength=INSIGHT
connection.timeoutInSecs=60
EOF

# 创建 AFL 配置
cat > ~/.safeflow/tools/afl.conf << 'EOF
# SafeFlow AFL 配置
timeout = 300
memory_limit = 512
cpu_limit = 1
```

### 环境变量

创建 `.env` 文件：

```bash
# ~/.safeflow/.env
# SafeFlow 工具配置

# Semgrep
SEMGREPCONFIG_PATH=~/.safeflow/tools/semgrep.yaml
SEMGREPRULESDIR=~/.safeflow/tools/rules

# Trivy
TRIVYCONFIGFILE=~/.safeflow/tools/trivy.yaml
TRIVYDB=~/.trivy/db

# OWASP ZAP
ZAPHOME=~/bin/ZAP_2.16.1
ZAPCONFIG=~/.safeflow/tools/zap.properties
ZAPPORT=8080

# AFL++
AFL_CONFIG=~/.safeflow/tools/afl.conf
AFL_OUTPUT_DIR=~/.safeflow/afl/output

# 通用
LOG_LEVEL=INFO
RESULTS_DIR=~/.safeflow/results
TEMP_DIR=~/.safeflow/temp
```

### 集成脚本

创建工具集成脚本：

```bash
#!/bin/bash
# ~/.safeflow/tools/run-scan.sh
# SafeFlow 工具集成脚本

set -e

# 加载环境变量
source ~/.safeflow/.env

# 创建结果目录
mkdir -p $RESULTS_DIR $TEMP_DIR

# 参数检查
if [ $# -lt 1 ]; then
    echo "Usage: $0 <target_path> [scan_type]"
    echo "Scan types: sast, dast, sca, fuzzing"
    exit 1
fi

TARGET_PATH=$1
SCAN_TYPE=${2:-"all"}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔍 SafeFlow 扫描开始..."
echo "目标路径: $TARGET_PATH"
echo "扫描类型: $SCAN_TYPE"
echo "结果目录: $RESULTS_DIR"

# 根据扫描类型执行相应工具
case $SCAN_TYPE in
    "sast" | "all")
        echo "📊 执行 Semgrep 静态分析..."
        semgrep --config=$SEMGREPCONFIG_PATH \
                --output=$RESULTS_DIR/semgrep_${TIMESTAMP}.json \
                $TARGET_PATH
        ;;
esac

case $SCAN_TYPE in
    "sca" | "all")
        echo "🛡️ 执行 Trivy 依赖扫描..."
        trivy fs --config=$TRIVYCONFIGFILE \
               --output=$RESULTS_DIR/trivy_${TIMESTAMP}.json \
               $TARGET_PATH
        ;;
esac

# 生成报告摘要
echo ""
echo "📋 扫描结果摘要:"
ls -la $RESULTS_DIR/*_${TIMESTAMP}.json

echo "✅ 扫描完成！"
```

## 📚 参考资料

- [Semgrep 官方文档](https://semgrep.dev/docs/)
- [Trivy 官方文档](https://aquasecurity.github.io/trivy/)
- [OWASP ZAP 官方文档](https://www.zaproxy.org/)
- [AFL++ 官方文档](https://github.com/AFLplusplus/AFLplusplus)
- [SafeFlow 项目文档](../README.md)
- [SafeFlow PRD 文档](../docs/prd.md)

## 🆘 获取帮助

如果在安装过程中遇到问题，请：

1. 查看本文档的常见问题部分
2. 访问 SafeFlow GitHub 仓库
3. 提交 Issue 或 Discussion
4. 联系 SafeFlow 开发团队

---

**最后更新**: 2025年11月30日
**版本**: v1.0.0