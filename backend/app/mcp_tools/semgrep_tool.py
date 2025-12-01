"""
Semgrep MCP 工具实现
静态代码分析工具的 MCP 封装
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

from app.core.mcp_base import (
    ExecutionContext,
    ExecutionResult,
    MCPToolBase,
    ParameterType,
    ToolCapability,
    ToolCategory,
    ToolParameter,
)

logger = logging.getLogger(__name__)


class SemgrepMCPTool(MCPToolBase):
    """Semgrep 静态代码分析工具"""

    def __init__(self):
        super().__init__()
        self.name = "semgrep"
        self.semgrep_path = self._find_semgrep_path()

    def _find_semgrep_path(self) -> Optional[str]:
        """查找 Semgrep 可执行文件路径"""
        # 检查常见路径
        paths = [
            "semgrep",  # PATH 中
            os.path.expanduser("~/.local/bin/semgrep"),  # 用户级安装
            os.path.expanduser("~/bin/semgrep"),  # 自定义安装
            "/opt/semgrep/semgrep",  # 系统级安装
        ]

        for path in paths:
            if os.path.exists(path) or os.path.exists(os.path.expanduser(path)):
                return path

        # 在 PATH 中查找
        try:
            result = subprocess.run(
                ["which", "semgrep"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    @property
    def parameters(self) -> List[ToolParameter]:
        """获取 Semgrep 参数定义"""
        return [
            ToolParameter(
                name="target_path",
                type=ParameterType.STRING,
                description="要扫描的文件或目录路径（必须参数）。示例：'.'（当前目录）、'/path/to/project'、'src/'、'app.py'",
                required=True,
                pattern=r"^[^<>:\"|?*\x00-\x1F]+$",
                min_length=1,
                max_length=1000,
            ),
            ToolParameter(
                name="config",
                type=ParameterType.STRING,
                description="Semgrep规则配置（默认: auto）。可选：'auto'（自动选择）、'p/security-audit'（安全审计）、'p/owasp-top-ten'（OWASP Top 10）、'p/cwe-top-25'（CWE Top 25）、'p/secrets'（敏感信息检测）",
                required=False,
                default="auto",
                enum=[
                    "auto",
                    "p/security-audit",
                    "p/owasp-top-ten",
                    "p/cwe-top-25",
                    "p/secrets",
                ],
                format="semgrep-config",
            ),
            ToolParameter(
                name="language",
                type=ParameterType.STRING,
                description="指定编程语言（仅用于文档说明）。Semgrep 会自动检测文件语言，不支持命令行语言过滤。如需过滤特定语言文件，请使用 include 参数，例如：'*.py'",
                required=False,
                enum=[
                    "python",
                    "javascript",
                    "typescript",
                    "java",
                    "go",
                    "ruby",
                    "php",
                    "c",
                    "cpp",
                    "csharp",
                ],
                format="language-code",
            ),
            ToolParameter(
                name="severity",
                type=ParameterType.STRING,
                description="最小严重性级别过滤（默认: INFO）。可选：'ERROR'（仅错误）、'WARNING'（警告及以上）、'INFO'（全部）",
                required=False,
                default="INFO",
                enum=["ERROR", "WARNING", "INFO"],
            ),
            ToolParameter(
                name="output_format",
                type=ParameterType.STRING,
                description="输出格式（默认: json）。推荐使用'json'便于解析，可选'sarif'（标准安全报告格式）、'text'（纯文本）",
                required=False,
                default="json",
                enum=["json", "sarif", "text", "junit-xml"],
            ),
            ToolParameter(
                name="max_memory",
                type=ParameterType.INTEGER,
                description="最大内存使用量限制（MB，默认: 1024）。大型项目建议增加此值，范围：256-8192",
                required=False,
                default=1024,
                minimum=256,
                maximum=8192,
            ),
            ToolParameter(
                name="timeout",
                type=ParameterType.INTEGER,
                description="扫描超时时间（秒，默认: 300）。大型项目建议增加此值，范围：10-3600",
                required=False,
                default=300,
                minimum=10,
                maximum=3600,
            ),
            ToolParameter(
                name="exclude",
                type=ParameterType.ARRAY,
                description="要排除的文件模式列表（可选，使用 Glob 模式）。例如：'*.test.js'、'**/test_*.py'、'node_modules'、'__pycache__'",
                required=False,
                default=["*.test.js", "*.spec.ts", "node_modules", "vendor", ".git"],
            ),
            ToolParameter(
                name="include",
                type=ParameterType.ARRAY,
                description="要包含的文件模式列表（可选，使用 Glob 模式）。例如：'*.py'（仅Python文件）、'src/**'（src目录下所有文件）、'**/*.js'（所有JS文件）",
                required=False,
                default=[],
            ),
            ToolParameter(
                name="enable_metrics",
                type=ParameterType.BOOLEAN,
                description="是否启用性能指标收集",
                required=False,
                default=True,
            ),
        ]

    @property
    def capability(self) -> ToolCapability:
        """获取 Semgrep 能力描述"""
        return ToolCapability(
            category=ToolCategory.STATIC_ANALYSIS,
            description=(
                "Semgrep 是一个快速的静态分析工具，用于在代码中发现漏洞和安全问题。"
                "支持多种编程语言，具有可定制的规则集，能够检测常见的安全漏洞模式、"
                "代码质量问题和不安全编码实践。集成了 OWASP Top Ten、CWE Top 25 等标准规则集。"
            ),
            version="1.144.0",
            author="Return To Corporation",
            homepage="https://semgrep.dev",
            documentation="https://semgrep.dev/docs/",
            supported_languages=[
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "Go",
                "Ruby",
                "PHP",
                "C",
                "C++",
                "C#",
                "Rust",
                "Kotlin",
                "Scala",
            ],
            supported_formats=["source_code", "text_files"],
            output_formats=["json", "sarif", "text", "junit-xml"],
            tags=[
                "static_analysis",
                "security",
                "sast",
                "vulnerability_detection",
                "code_quality",
                "owasp",
                "cwe",
                "multi_language",
            ],
        )

    async def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证 Semgrep 参数"""
        try:
            # 检查必需参数
            if "target_path" not in args:
                logger.error("Missing required parameter: target_path")
                return False

            target_path = args["target_path"]

            # 验证目标路径（考虑执行上下文的工作目录）
            # 注意：实际的路径解析会在 execute 方法中使用 context.workspace_dir
            # 这里只做基本验证，不检查文件是否存在（因为工作目录可能不同）
            if not target_path or not isinstance(target_path, str):
                logger.error(f"Invalid target_path: {target_path}")
                return False

            # 检查路径是否包含危险字符
            if any(char in target_path for char in ["<", ">", "|", "&", ";", "`", "$"]):
                logger.error(
                    f"Target path contains dangerous characters: {target_path}"
                )
                return False

            # 验证配置参数
            if "config" in args:
                config = args["config"]
                if config.startswith("/") and not os.path.exists(config):
                    logger.error(f"Config file does not exist: {config}")
                    return False

            # 验证语言参数
            if "language" in args:
                languages = (
                    args["language"].split(",")
                    if isinstance(args["language"], str)
                    else args["language"]
                )
                valid_languages = [
                    param.enum for param in self.parameters if param.name == "language"
                ][0]
                for lang in languages:
                    if lang.strip() not in valid_languages:
                        logger.error(f"Invalid language: {lang}")
                        return False

            # 验证输出格式
            if "output_format" in args:
                valid_formats = [
                    param.enum
                    for param in self.parameters
                    if param.name == "output_format"
                ][0]
                if args["output_format"] not in valid_formats:
                    logger.error(f"Invalid output format: {args['output_format']}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating args: {str(e)}")
            return False

    async def check_availability(self) -> bool:
        """检查 Semgrep 可用性"""
        if not self.semgrep_path:
            logger.error("Semgrep not found in PATH")
            return False

        try:
            # 检查 Semgrep 是否可执行
            result = subprocess.run(
                [self.semgrep_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.error(f"Semgrep version check failed: {result.stderr}")
                return False

            version = result.stdout.strip()
            logger.info(f"Semgrep available: {version}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Semgrep version check timed out")
            return False
        except Exception as e:
            logger.error(f"Semgrep availability check failed: {str(e)}")
            return False

    async def execute(
        self, args: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """执行 Semgrep 扫描"""
        start_time = time.time()

        try:
            # 准备命令
            cmd = [self.semgrep_path]

            # 添加配置参数
            config = args.get("config", "auto")
            if config == "auto":
                cmd.extend(["--config=auto"])
            elif config.startswith("p/"):
                cmd.extend([f"--config={config}"])
            else:
                # 自定义配置文件
                cmd.extend([f"--config={config}"])

            # 添加输出格式
            output_format = args.get("output_format", "json")
            cmd.extend([f"--{output_format}"])

            # 注意：--lang 参数必须与 -e/--pattern 一起使用，在扫描模式下不能单独使用
            # Semgrep 会自动检测文件语言，所以我们不在命令行中强制指定语言
            # if "language" in args:
            #     logger.info(f"Language filter specified: {args['language']} (Semgrep will auto-detect)")
            #     # 语言过滤通过 --include 模式来实现，例如 --include="*.py" 来扫描 Python 文件

            # 添加严重性过滤
            if "severity" in args:
                cmd.extend([f"--severity={args['severity']}"])

            # 添加排除模式
            if "exclude" in args and args["exclude"]:
                for pattern in args["exclude"]:
                    cmd.extend([f"--exclude={pattern}"])

            # 添加包含模式
            if "include" in args and args["include"]:
                for pattern in args["include"]:
                    cmd.extend([f"--include={pattern}"])

            # 添加性能指标 - 注意：auto 配置需要 metrics，所以只有在非 auto 配置时才关闭 metrics
            config = args.get("config", "auto")
            if config != "auto" and args.get("enable_metrics", True):
                cmd.extend(["--metrics=off"])  # 禁用默认指标，我们自行收集

            # 添加内存限制
            if "max_memory" in args:
                # Semgrep 不直接支持内存限制，这里仅为记录
                logger.info(f"Memory limit set to {args['max_memory']}MB")

            # 添加目标路径
            cmd.append(args["target_path"])

            logger.info(f"Executing Semgrep: {' '.join(cmd)}")

            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f".{output_format}", delete=False
            ) as tmp_file:
                output_file = tmp_file.name

            # 重定向输出
            cmd.extend([f"--output={output_file}"])

            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.workspace_dir or os.getcwd(),
            )

            # 设置超时
            timeout = args.get("timeout", context.timeout)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                execution_time = time.time() - start_time
                return self.create_error_result(
                    tool_name=self.name,
                    error=f"Semgrep execution timed out after {timeout} seconds",
                    execution_time=execution_time,
                )

            execution_time = time.time() - start_time

            # 读取输出文件
            output_content = None
            if os.path.exists(output_file):
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        output_content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read output file: {str(e)}")

            # 清理临时文件
            try:
                os.unlink(output_file)
            except Exception:
                pass

            # 检查执行结果
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                logger.error(f"Semgrep execution failed: {error_msg}")
                return self.create_error_result(
                    tool_name=self.name, error=error_msg, execution_time=execution_time
                )

            # 解析结果统计
            metadata = {}
            if output_content and output_format == "json":
                try:
                    result_data = json.loads(output_content)
                    metadata = {
                        "rules_run": result_data.get("paths", {}).get(
                            "scanned_files_count", 0
                        ),
                        "files_scanned": len(
                            result_data.get("paths", {}).get("scanned", [])
                        ),
                        "findings_count": len(result_data.get("results", [])),
                        "version": result_data.get("version", "unknown"),
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse JSON output: {str(e)}")

            logger.info(f"Semgrep execution completed in {execution_time:.2f}s")

            return self.create_success_result(
                tool_name=self.name,
                execution_time=execution_time,
                output=output_content,
                metadata=metadata,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Unexpected error in Semgrep execution: {str(e)}")
            return self.create_error_result(
                tool_name=self.name, error=str(e), execution_time=execution_time
            )

    async def get_version_info(self) -> Optional[str]:
        """获取 Semgrep 版本信息"""
        try:
            result = subprocess.run(
                [self.semgrep_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    async def get_available_configs(self) -> List[str]:
        """获取可用的配置列表"""
        try:
            result = subprocess.run(
                [self.semgrep_path, "--list-configs"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # 解析配置列表
                configs = []
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        configs.append(line)
                return configs
            return []
        except Exception:
            return []
