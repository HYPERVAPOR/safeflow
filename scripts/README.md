# SafeFlow 安全工具安装脚本

本目录包含针对不同操作系统的 SafeFlow 安全工具自动安装脚本，具备完善的回退机制和错误处理能力。

## 📁 脚本列表

| 操作系统 | 脚本文件 | 说明 |
|---------|---------|------|
| **Linux** | [`install-tools-linux.sh`](./install-tools-linux.sh) | 支持 Ubuntu、CentOS、Fedora、Arch 等 |
| **macOS** | [`install-tools-mac.sh`](./install-tools-mac.sh) | 支持 Intel 和 Apple Silicon |
| **Windows** | [`install-tools-windows.bat`](./install-tools-windows.bat) | 支持 Windows 10/11 |

## 🚀 快速开始

### Linux 用户
```bash
# 克隆或下载脚本
wget https://raw.githubusercontent.com/your-repo/safeflow/main/scripts/install-tools-linux.sh

# 运行安装脚本
chmod +x install-tools-linux.sh
./install-tools-linux.sh

# 验证安装
~/.safeflow/verify-installation.sh
```

### macOS 用户
```bash
# 克隆或下载脚本
curl -O https://raw.githubusercontent.com/your-repo/safeflow/main/scripts/install-tools-mac.sh

# 运行安装脚本
chmod +x install-tools-mac.sh
./install-tools-mac.sh

# 验证安装
~/.safeflow/verify-installation.sh
```

### Windows 用户
```batch
REM 下载并运行安装脚本
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/your-repo/safeflow/main/scripts/install-tools-windows.bat' -OutFile 'install-tools-windows.bat'"
install-tools-windows.bat

REM 验证安装
%safeflow%\verify-installation.bat
```

## 🛠️ 安装的工具

### 核心工具（必须安装）
- **Semgrep** - 静态代码分析工具
- **Trivy** - 漏洞扫描工具
- **OWASP ZAP** - Web 应用安全测试工具

### 可选工具
- **AFL++** - 模糊测试工具

## 🔧 回退机制

每个脚本都包含多层回退机制，确保在不同环境下都能成功安装：

### Semgrep 安装策略
1. **主要方式**: pip3 install --user semgrep
2. **回退1**: sudo pip3 install semgrep
3. **回退2**: Python 虚拟环境安装
4. **回退3**: 直接下载二进制文件

### Trivy 安装策略
1. **主要方式**: 官方安装脚本
2. **回退1**: 手动下载 GitHub Release
3. **回退2**: 系统包管理器（apt/yum/brew）
4. **回退3**: Docker 容器

### OWASP ZAP 安装策略
1. **主要方式**: 直接下载 GitHub Release
2. **回退1**: 系统包管理器
3. **回退2**: Docker 容器
4. **回退3**: 使用包管理器 Cask（macOS）

## 📋 系统要求

### 最低要求
- **操作系统**: Linux (Ubuntu 18.04+), macOS (10.15+), Windows 10+
- **内存**: 2GB RAM（推荐 4GB+）
- **存储**: 2GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐环境
- **Java**: 11+（OWASP ZAP 需要）
- **Python**: 3.8+
- **Docker**: 最新版本（可选）

## ⚡ 特性

### 🛡️ 安全性
- 不使用 root 权限运行（Linux/macOS）
- 用户目录隔离安装
- 自动权限设置

### 🔄 自动化
- 智能系统检测
- 自动依赖安装
- 环境变量配置
- PATH 自动更新

### 🎯 容错性
- 多种安装方法回退
- 网络错误处理
- 权限问题检测
- 详细错误提示

### 📊 验证机制
- 安装后自动验证
- 功能测试确保工具可用
- 版本信息显示
- 配置状态检查

## 🐛 故障排除

### 常见问题

**Q: 脚本运行失败，提示权限不足**
```bash
# Linux/macOS
chmod +x install-tools-*.sh

# Windows: 以管理员身份运行命令提示符
```

**Q: 网络连接问题导致下载失败**
- 检查防火墙设置
- 尝试使用代理
- 手动下载工具并安装到 `~/bin` 或 `%USERPROFILE%\safeflow\bin`

**Q: Java 环境问题**
```bash
# Linux
sudo apt install openjdk-11-jdk
# 或
sudo yum install java-11-openjdk

# macOS
brew install openjdk@11

# Windows: 从 https://adoptium.net/ 下载
```

**Q: Python 环境问题**
```bash
# Linux
sudo apt install python3 python3-pip

# macOS
brew install python3

# Windows: 从 Microsoft Store 安装 Python
```

### 手动安装回退

如果自动脚本完全失败，可以参考以下文档手动安装：

- [详细安装指南](../docs/tool-installation-guide.md)
- [官方文档链接](#官方文档)

## 📚 官方文档

- [Semgrep 官方文档](https://semgrep.dev/docs/)
- [Trivy 官方文档](https://aquasecurity.github.io/trivy/)
- [OWASP ZAP 官方文档](https://www.zaproxy.org/)
- [AFL++ 官方文档](https://github.com/AFLplusplus/AFLplusplus)
- [SafeFlow 项目文档](../README.md)

## 🆘 获取帮助

如果遇到问题：

1. **查看日志**: 脚本会显示详细的错误信息
2. **运行验证**: 使用 `verify-installation.sh/bat` 检查状态
3. **查看文档**: 参考 [安装指南](../docs/tool-installation-guide.md)
4. **提交问题**: 在 GitHub 仓库创建 Issue

## 🔄 更新

### 更新工具
```bash
# Semgrep
pip install --upgrade semgrep

# Trivy
trivy image --download-db

# OWASP ZAP
# 在 ZAP GUI 中进行更新
```

### 重新运行安装脚本
```bash
./install-tools-$(uname).sh
```

脚本会检测已安装的工具并跳过相关步骤。

## 📄 许可证

本安装脚本遵循 SafeFlow 项目的许可证条款。各工具的许可证请参考各自的官方文档。

---

**最后更新**: 2025年11月30日
**版本**: v1.0.0
**适用范围**: SafeFlow 智能测试平台