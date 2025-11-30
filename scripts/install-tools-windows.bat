@echo off
REM SafeFlow 安全工具安装脚本 - Windows 版本
REM 包含各种回退机制和错误处理
REM 支持 PowerShell 和 Chocolatey 安装方式

setlocal enabledelayedexpansion

echo.
echo 🚀 SafeFlow 安全工具安装脚本 - Windows 版本
echo ================================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ⚠️  检测到管理员权限，建议使用普通用户运行
    pause
)

REM 设置变量
set SAFEFLOW_DIR=%USERPROFILE%\safeflow
set SAFEFLOW_BIN=%SAFEFLOW_DIR%\bin
set TEMP_DIR=%TEMP%\safeflow-install

echo 📁 设置目录结构...
if not exist "%SAFEFLOW_DIR%" mkdir "%SAFEFLOW_DIR%"
if not exist "%SAFEFLOW_BIN%" mkdir "%SAFEFLOW_BIN%"
if not exist "%SAFEFLOW_DIR%\tools" mkdir "%SAFEFLOW_DIR%\tools"
if not exist "%SAFEFLOW_DIR%\temp" mkdir "%SAFEFLOW_DIR%\temp"
if not exist "%SAFEFLOW_DIR%\results" mkdir "%SAFEFLOW_DIR%\results"

REM 检查网络连接
echo 🌐 检查网络连接...
ping -n 1 google.com >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  网络连接可能有问题，某些下载可能失败
) else (
    echo ✅ 网络连接正常
)

REM 添加到 PATH
echo 🔧 配置环境变量...
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul ^| findstr "PATH"') do (
    echo !PATH! | findstr /C:"%SAFEFLOW_BIN%" >nul
    if !errorLevel! neq 0 (
        setx PATH "%SAFEFLOW_BIN%;%%B" >nul
        echo 已将 %SAFEFLOW_BIN% 添加到 PATH
    )
)

REM 安装 Python (如果不存在)
echo 🐍 检查 Python 环境...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Python 未安装，尝试安装...

    REM 方法1: Microsoft Store (推荐)
    echo 方法1: 尝试从 Microsoft Store 安装 Python...
    start ms-store://pdp/?ProductId=9P7QFQMJRFP7
    echo 请在 Microsoft Store 中安装 Python 3.11+，然后按任意键继续...
    pause

    REM 方法2: 官方下载 (回退)
    python --version >nul 2>&1
    if !errorLevel! neq 0 (
        echo 方法2: 下载 Python 安装包...
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
        if exist "%TEMP%\python-installer.exe" (
            echo 请运行 %TEMP%\python-installer.exe 安装 Python
            echo 安装时请勾选 "Add Python to PATH"
            start "" "%TEMP%\python-installer.exe"
            echo 安装完成后按任意键继续...
            pause
        )
    )
) else (
    echo ✅ Python 已安装
    for /f "tokens=2" %%V in ('python --version 2^>^&1') do echo 版本: %%V
)

REM 检查 Git
echo 📦 检查 Git...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Git 未安装，尝试安装...

    REM 方法1: GitHub Desktop
    echo 方法1: 尝试安装 GitHub Desktop...
    start ms-store://pdp/?ProductId=9NBLGGH4N4T1
    echo 请在 Microsoft Store 中安装 GitHub Desktop，然后按任意键继续...
    pause

    REM 方法2: Git for Windows (回退)
    git --version >nul 2>&1
    if !errorLevel! neq 0 (
        echo 方法2: 下载 Git for Windows...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe' -OutFile '%TEMP%\git-installer.exe'"
        if exist "%TEMP%\git-installer.exe" (
            start "" "%TEMP%\git-installer.exe"
            echo 安装完成后按任意键继续...
            pause
        )
    )
) else (
    echo ✅ Git 已安装
)

REM 检查 Java
echo ☕ 检查 Java 环境...
java -version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Java 未安装，OWASP ZAP 将无法使用
    echo 建议安装 Java 11+，可以从 https://adoptium.net/ 下载
    echo 或者在 Microsoft Store 搜索 "Eclipse Adoptium"
) else (
    echo ✅ Java 已安装
)

REM 检查 PowerShell 版本
echo 🔍 检查 PowerShell...
powershell -Command "Get-Host" | findstr "Version" >nul
echo PowerShell 版本检查完成

REM 安装 Chocolatey (可选)
echo 🍫 检查 Chocolatey 包管理器...
choco --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Chocolatey 未安装，尝试安装...
    echo 如需安装 Chocolatey，请以管理员身份运行以下命令：
    echo Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    echo.
    set CHOCO_AVAILABLE=false
) else (
    echo ✅ Chocolatey 已安装
    set CHOCO_AVAILABLE=true
)

REM 安装 Semgrep
echo 📊 安装 Semgrep (静态代码分析工具)...

REM 方法1: pip (推荐)
python -m pip --version >nul 2>&1
if !errorLevel! neq 0 (
    echo 方法1: 使用 pip 安装 Semgrep...
    python -m pip install --user semgrep
    if !errorLevel! neq 0 (
        echo ✅ pip 安装成功
    ) else (
        echo ⚠️  pip 安装失败，尝试其他方法
    )
)

REM 方法2: Chocolatey (回退)
semgrep --version >nul 2>&1
if !errorLevel! neq 0 (
    if "!CHOCO_AVAILABLE!"=="true" (
        echo 方法2: 使用 Chocolatey 安装...
        choco install semgrep
        if !errorLevel! neq 0 (
            echo ✅ Chocolatey 安装成功
        ) else (
            echo ⚠️  Chocolatey 安装失败
        )
    )
)

REM 方法3: 手动下载 (回退)
semgrep --version >nul 2>&1
if !errorLevel! neq 0 (
    echo 方法3: 手动下载 Semgrep...
    if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

    powershell -Command "try { $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/returntocorp/semgrep/releases/latest'; $version = $response.tag_name; Write-Output $version } catch { Write-Output '' }" >"%TEMP%\semgrep-version.txt"

    set /p SEMGREP_VERSION=<"%TEMP%\semgrep-version.txt"
    if not "!SEMGREP_VERSION!"=="" (
        echo 下载版本: !SEMGREP_VERSION!
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/returntocorp/semgrep/releases/download/!SEMGREP_VERSION!/semgrep-v0-windows.exe' -OutFile '%SAFEFLOW_BIN%\semgrep.exe'"
        if exist "%SAFEFLOW_BIN%\semgrep.exe" (
            echo ✅ 手动下载成功
        ) else (
            echo ❌ 手动下载失败
        )
    )
)

REM 验证 Semgrep
semgrep --version >nul 2>&1
if !errorLevel! neq 0 (
    echo ✅ Semgrep 安装成功
    for /f "tokens=2" %%V in ('semgrep --version 2^>^&1') do echo 版本: %%V
) else (
    echo ❌ Semgrep 安装失败
)

REM 安装 Trivy
echo 🛡️  安装 Trivy (漏洞扫描工具)...

REM 方法1: Chocolatey (推荐)
if "!CHOCO_AVAILABLE!"=="true" (
    echo 方法1: 使用 Chocolatey 安装...
    choco install trivy
    if !errorLevel! neq 0 (
        echo ✅ Chocolatey 安装成功
    ) else (
        echo ⚠️  Chocolatey 安装失败，尝试其他方法
    )
)

REM 方法2: 手动下载 (回退)
trivy --version >nul 2>&1
if !errorLevel! neq 0 (
    echo 方法2: 手动下载 Trivy...
    if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

    powershell -Command "try { $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/aquasecurity/trivy/releases/latest'; $version = $response.tag_name; Write-Output $version } catch { Write-Output '' }" >"%TEMP%\trivy-version.txt"

    set /p TRIVY_VERSION=<"%TEMP%\trivy-version.txt"
    if not "!TRIVY_VERSION!"=="" (
        echo 下载版本: !TRIVY_VERSION!
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/aquasecurity/trivy/releases/download/!TRIVY_VERSION!/trivy_!TRIVY_VERSION:v=1!_Windows-64bit.zip' -OutFile '%TEMP_DIR%\trivy.zip'"

        if exist "%TEMP_DIR%\trivy.zip" (
            powershell -Command "Expand-Archive -Path '%TEMP_DIR%\trivy.zip' -DestinationPath '%SAFEFLOW_BIN%' -Force"
            if exist "%SAFEFLOW_BIN%\trivy.exe" (
                echo ✅ 手动下载成功
            ) else (
                echo ❌ 解压失败
            )
        )
    )
)

REM 方法3: 使用 Scoop (回退)
trivy --version >nul 2>&1
if !errorLevel! neq 0 (
    echo 方法3: 检查是否可以使用 Scoop 安装...
    scoop --version >nul 2>&1
    if !errorLevel! neq 0 (
        scoop install trivy
        if !errorLevel! neq 0 (
            echo ✅ Scoop 安装成功
        )
    )
)

REM 验证 Trivy
trivy --version >nul 2>&1
if !errorLevel! neq 0 (
    echo ✅ Trivy 安装成功
    for /f "tokens=2" %%V in ('trivy --version 2^>^&1') do echo 版本: %%V
) else (
    echo ❌ Trivy 安装失败
)

REM 安装 OWASP ZAP
echo 🕷️  安装 OWASP ZAP (Web 应用安全测试工具)...

REM 检查 Java
java -version >nul 2>&1
if !errorLevel! neq 0 (
    echo ✅ Java 环境可用，安装 OWASP ZAP...

    REM 方法1: 手动下载
    if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

    powershell -Command "try { $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/zaproxy/zaproxy/releases/latest'; $version = $response.tag_name; Write-Output $version } catch { Write-Output '' }" >"%TEMP%\zap-version.txt"

    set /p ZAP_VERSION=<"%TEMP%\zap-version.txt"
    if not "!ZAP_VERSION!"=="" (
        echo 下载版本: !ZAP_VERSION!
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/zaproxy/zaproxy/releases/download/!ZAP_VERSION!/ZAP_!ZAP_VERSION!_Windows.exe' -OutFile '%TEMP_DIR%\ZAP_Installer.exe'"

        if exist "%TEMP_DIR%\ZAP_Installer.exe" (
            echo 请运行 %TEMP_DIR%\ZAP_Installer.exe 安装 OWASP ZAP
            echo 安装完成后，ZAP 将在 Start Menu 中可用
            start "" "%TEMP_DIR%\ZAP_Installer.exe"
            echo 安装完成后按任意键继续...
            pause
        )
    )

    REM 方法2: Chocolatey (回退)
    if "!CHOCO_AVAILABLE!"=="true" (
        echo 方法2: 使用 Chocolatey 安装...
        choco install zaproxy
        if !errorLevel! neq 0 (
            echo ✅ Chocolatey 安装成功
        )
    )

    REM 方法3: Docker (回退)
    docker --version >nul 2>&1
    if !errorLevel! neq 0 (
        echo 方法3: 使用 Docker 运行 OWASP ZAP...
        docker pull owasp/zap2docker-stable

        REM 创建 Docker 脚本
        echo @echo off > "%SAFEFLOW_BIN%\zap-docker.bat"
        echo docker run --rm -it -v "%%cd%%:C:/zap/wrk/" owasp/zap2docker-stable zap.bat %%* >> "%SAFEFLOW_BIN%\zap-docker.bat"
        echo ✅ Docker 脚本已创建: %SAFEFLOW_BIN%\zap-docker.bat
    )

) else (
    echo ⚠️  Java 未安装，跳过 OWASP ZAP 安装
    echo 请先安装 Java 11+ 后再运行此脚本
)

REM 创建验证脚本
echo 📋 创建验证脚本...

(
echo @echo off
echo.
echo 🔍 SafeFlow 工具安装验证 ^(Windows^)
echo =====================================
echo.
echo setlocal enabledelayedexpansion
echo set total=0
echo set passed=0
echo.
echo verify^(name, cmd^)
echo     set /a total+=1
echo     echo -n 验证 %%name^^^>^&2 ...
echo
echo     %%cmd^^^>nul 2^^>^^&1
echo     if !errorLevel! neq 0 ^(
echo         echo ✅ 通过^^^>^&2
echo         set /a passed+=1
echo     ^) else ^(
echo         echo ❌ 失败^^^>^&2
echo     ^^)
echo )
echo.
echo echo import os; os.system^(\"echo test\"^) ^> test_vuln.py
echo.
echo verify \"Semgrep\" \"semgrep --version\"
echo verify \"Trivy\" \"trivy --version\"
echo verify \"Java 环境\" \"java -version\"
echo verify \"Git\" \"git --version\"
echo.
echo del test_vuln.py 2^>nul
echo.
echo echo.
echo echo 📊 验证结果: !passed!/!total! 通过
echo.
echo echo 工具版本信息:
echo semgrep --version 2^>nul ^&^& echo   Semgrep: %%^^(semgrep --version^)^^%
echo trivy --version 2^>nul ^&^& echo   Trivy: %%^^(trivy --version^)^^%
echo java -version 2^>^&1 ^&^& echo   Java: %%^^(java -version 2^>^&1 ^| head -1^)^^%
echo git --version 2^>nul ^&^& echo   Git: %%^^(git --version^)^^%
echo.
) > "%SAFEFLOW_DIR%\verify-installation.bat"

echo ✅ 验证脚本已创建: %SAFEFLOW_DIR%\verify-installation.bat

REM 创建启动脚本
echo 🚀 创建启动脚本...

(
echo @echo off
echo.
echo 🚀 SafeFlow 工具快速启动
echo ========================
echo.
echo if \"%%1\"==\"\" goto :help
echo goto :%%1
echo.
echo :semgrep
echo     semgrep %%2 %%3 %%4 %%5 %%6 %%7 %%8 %%9
echo     goto :end
echo.
echo :trivy
echo     trivy %%2 %%3 %%4 %%5 %%6 %%7 %%8 %%9
echo     goto :end
echo.
echo :verify
echo     call \"%SAFEFLOW_DIR%\verify-installation.bat\"
echo     goto :end
echo.
echo :help
echo     echo 用法:
echo     echo   tools.bat semgrep [参数] - 运行 Semgrep
echo     echo   tools.bat trivy [参数]  - 运行 Trivy
echo     echo   tools.bat verify        - 验证安装
echo     echo.
echo     echo 示例:
echo     echo   tools.bat semgrep --config=auto C:\project
echo     echo   tools.bat trivy fs C:\project
echo     echo   tools.bat verify
echo.
echo :end
) > "%SAFEFLOW_BIN%\tools.bat"

echo ✅ 启动脚本已创建: %SAFEFLOW_BIN%\tools.bat

REM 清理临时文件
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" 2>nul

echo.
echo 🎉 安装脚本执行完成！
echo.
echo 📋 后续步骤:
echo   1. 重新打开命令提示符或 PowerShell
echo   2. 运行验证脚本: %SAFEFLOW_DIR%\verify-installation.bat
echo   3. 使用工具启动器: %SAFEFLOW_BIN%\tools.bat
echo   4. 查看安装指南: https://github.com/your-repo/safeflow/docs/tool-installation-guide.md
echo.
echo ⚠️  Windows 特别注意事项:
echo   - 某些工具可能需要管理员权限
echo   - Windows Defender 可能误报安全工具，请添加例外
echo   - 防火墙可能需要允许工具的网络访问
echo   - 首次运行时某些工具会自动下载数据库
echo   - PowerShell 执行策略可能需要调整
echo.
echo 📚 更多信息请参考 SafeFlow 文档

pause