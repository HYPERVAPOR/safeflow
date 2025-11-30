"""
Trivy MCP 工具实现
漏洞扫描工具的 MCP 封装
"""

import asyncio
import json
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

from app.core.mcp_base import (
    MCPToolBase, ToolCapability, ToolParameter, ParameterType,
    ToolCategory, ExecutionContext, ExecutionResult
)
import logging

logger = logging.getLogger(__name__)


class TrivyMCPTool(MCPToolBase):
    """Trivy 漏洞扫描工具"""

    def __init__(self):
        super().__init__()
        self.name = "trivy"
        self.trivy_path = self._find_trivy_path()

    def _find_trivy_path(self) -> Optional[str]:
        """查找 Trivy 可执行文件路径"""
        # 检查常见路径
        paths = [
            "trivy",  # PATH 中
            os.path.expanduser("~/.local/bin/trivy"),  # 用户级安装
            os.path.expanduser("~/bin/trivy"),  # 自定义安装
            "/usr/local/bin/trivy",  # 系统级安装
            "/opt/trivy/trivy",  # 自定义安装
        ]

        for path in paths:
            if os.path.exists(path) or os.path.exists(os.path.expanduser(path)):
                return path

        # 在 PATH 中查找
        try:
            result = subprocess.run(["which", "trivy"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    @property
    def parameters(self) -> List[ToolParameter]:
        """获取 Trivy 参数定义"""
        return [
            ToolParameter(
                name="target",
                type=ParameterType.STRING,
                description="扫描目标：文件路径(fs:)、镜像名称(image:)、Git仓库(repo:)等",
                required=True,
                min_length=1,
                max_length=1000,
                format="trivy-target"
            ),
            ToolParameter(
                name="scan_type",
                type=ParameterType.STRING,
                description="扫描类型",
                required=False,
                default="fs",
                enum=["fs", "image", "repo", "config"],
                format="scan-type"
            ),
            ToolParameter(
                name="severity",
                type=ParameterType.ARRAY,
                description="漏洞严重性级别过滤",
                required=False,
                default=["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
                enum=["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
            ),
            ToolParameter(
                name="security_checks",
                type=ParameterType.ARRAY,
                description="安全检查类型",
                required=False,
                default=["vuln", "config"],
                enum=["vuln", "config", "secret", "license"]
            ),
            ToolParameter(
                name="output_format",
                type=ParameterType.STRING,
                description="输出格式",
                required=False,
                default="json",
                enum=["json", "table", "sarif", "cyclonedx", "spdx-json", "spdx-sbom", "coset-vuln"]
            ),
            ToolParameter(
                name="scanners",
                type=ParameterType.ARRAY,
                description="指定扫描器",
                required=False,
                default=[],
                enum=["vuln", "misconfig", "secret", "license"]
            ),
            ToolParameter(
                name="skip_dirs",
                type=ParameterType.ARRAY,
                description="跳过的目录列表",
                required=False,
                default=["vendor", "node_modules", ".git", ".svn", ".hg"]
            ),
            ToolParameter(
                name="skip_files",
                type=ParameterType.ARRAY,
                description="跳过的文件模式列表",
                required=False,
                default=["*.test.js", "*.spec.ts", "*.md", "*.txt"]
            ),
            ToolParameter(
                name="ignore_unfixed",
                type=ParameterType.BOOLEAN,
                description="是否忽略未修复的漏洞",
                required=False,
                default=False
            ),
            ToolParameter(
                name="ignore_file",
                type=ParameterType.STRING,
                description="忽略规则文件路径",
                required=False,
                default="",
                format="file-path"
            ),
            ToolParameter(
                name="timeout",
                type=ParameterType.INTEGER,
                description="扫描超时时间(秒)",
                required=False,
                default=600,
                minimum=30,
                maximum=3600
            ),
            ToolParameter(
                name="cache_dir",
                type=ParameterType.STRING,
                description="缓存目录路径",
                required=False,
                default="",
                format="directory-path"
            ),
            ToolParameter(
                name="list_all_packages",
                type=ParameterType.BOOLEAN,
                description="是否列出所有包（包括无漏洞的）",
                required=False,
                default=False
            ),
            ToolParameter(
                name="offline_scan",
                type=ParameterType.BOOLEAN,
                description="是否离线扫描（不更新数据库）",
                required=False,
                default=False
            )
        ]

    @property
    def capability(self) -> ToolCapability:
        """获取 Trivy 能力描述"""
        return ToolCapability(
            category=ToolCategory.DEPENDENCY_ANALYSIS,
            description=(
                "Trivy 是一个简单而全面的安全扫描器，能够检测容器镜像、文件系统、"
                "Git 仓库中的漏洞和配置错误。支持多种操作系统和编程语言的包管理器，"
                "集成 CVE 数据库、配置检查、密钥扫描、许可证检查等多种安全检查功能。"
                "具有速度快、误报率低、数据库更新及时等特点。"
            ),
            version="0.67.2",
            author="Aqua Security",
            homepage="https://github.com/aquasecurity/trivy",
            documentation="https://aquasecurity.github.io/trivy/",
            supported_languages=[
                "Go", "Python", "Java", "Node.js", "Ruby", "PHP", "Rust",
                "C/C++", ".NET", "Docker", "Kubernetes"
            ],
            supported_formats=[
                "filesystem", "container_image", "git_repository", "config_files"
            ],
            output_formats=[
                "json", "table", "sarif", "cyclonedx", "spdx", "coset-vuln"
            ],
            tags=[
                "vulnerability_scanner", "dependency_analysis", "container_security",
                "cve_database", "config_checking", "secret_scanning", "license_checking"
            ]
        )

    async def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证 Trivy 参数"""
        try:
            # 检查必需参数
            if "target" not in args:
                logger.error("Missing required parameter: target")
                return False

            target = args["target"]
            scan_type = args.get("scan_type", "fs")

            # 验证目标类型
            if scan_type == "fs":
                # 文件系统扫描
                if not os.path.exists(target):
                    logger.error(f"Target path does not exist: {target}")
                    return False
                if not os.access(target, os.R_OK):
                    logger.error(f"Target path is not readable: {target}")
                    return False

            elif scan_type == "image":
                # 容器镜像扫描
                if not target or len(target.strip()) == 0:
                    logger.error("Invalid image name")
                    return False

            elif scan_type == "repo":
                # Git 仓库扫描
                # 验证 URL 格式
                if not target.startswith(("http://", "https://", "git@")):
                    logger.error(f"Invalid repository URL: {target}")
                    return False

            # 验证输出格式
            if "output_format" in args:
                valid_formats = [param.enum for param in self.parameters if param.name == "output_format"][0]
                if args["output_format"] not in valid_formats:
                    logger.error(f"Invalid output format: {args['output_format']}")
                    return False

            # 验证严重性级别
            if "severity" in args:
                valid_severities = [param.enum for param in self.parameters if param.name == "severity"][0]
                for severity in args["severity"]:
                    if severity not in valid_severities:
                        logger.error(f"Invalid severity level: {severity}")
                        return False

            # 验证安全检查类型
            if "security_checks" in args:
                valid_checks = [param.enum for param in self.parameters if param.name == "security_checks"][0]
                for check in args["security_checks"]:
                    if check not in valid_checks:
                        logger.error(f"Invalid security check: {check}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating args: {str(e)}")
            return False

    async def check_availability(self) -> bool:
        """检查 Trivy 可用性"""
        if not self.trivy_path:
            logger.error("Trivy not found in PATH")
            return False

        try:
            # 检查 Trivy 是否可执行
            result = subprocess.run(
                [self.trivy_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.error(f"Trivy version check failed: {result.stderr}")
                return False

            version = result.stdout.strip()
            logger.info(f"Trivy available: {version}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Trivy version check timed out")
            return False
        except Exception as e:
            logger.error(f"Trivy availability check failed: {str(e)}")
            return False

    async def execute(self, args: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """执行 Trivy 扫描"""
        start_time = time.time()

        try:
            # 准备命令
            cmd = [self.trivy_path]
            scan_type = args.get("scan_type", "fs")

            # 添加扫描类型
            cmd.append(scan_type)

            # 添加输出格式
            output_format = args.get("output_format", "json")
            cmd.extend(["--format", output_format])

            # 添加安全检查类型
            security_checks = args.get("security_checks", ["vuln", "config"])
            if security_checks:
                cmd.extend(["--security-checks", ",".join(security_checks)])

            # 添加严重性过滤
            if "severity" in args:
                cmd.extend(["--severity", ",".join(args["severity"])])

            # 添加扫描器
            if "scanners" in args and args["scanners"]:
                cmd.extend(["--scanners", ",".join(args["scanners"])])

            # 跳过目录
            if "skip_dirs" in args and args["skip_dirs"]:
                for skip_dir in args["skip_dirs"]:
                    cmd.extend(["--skip-dirs", skip_dir])

            # 跳过文件
            if "skip_files" in args and args["skip_files"]:
                for skip_file in args["skip_files"]:
                    cmd.extend(["--skip-files", skip_file])

            # 忽略未修复漏洞
            if args.get("ignore_unfixed", False):
                cmd.append("--ignore-unfixed")

            # 忽略文件
            if "ignore_file" in args and args["ignore_file"]:
                if os.path.exists(args["ignore_file"]):
                    cmd.extend(["--ignorefile", args["ignore_file"]])
                else:
                    logger.warning(f"Ignore file not found: {args['ignore_file']}")

            # 列出所有包
            if args.get("list_all_packages", False):
                cmd.append("--list-all-pkgs")

            # 离线扫描
            if args.get("offline_scan", False):
                cmd.append("--offline-scan")

            # 缓存目录
            if "cache_dir" in args and args["cache_dir"]:
                if os.path.exists(args["cache_dir"]):
                    cmd.extend(["--cache-dir", args["cache_dir"]])
                else:
                    logger.warning(f"Cache directory not found: {args['cache_dir']}")

            # 静默模式
            cmd.append("--quiet")

            # 添加目标
            cmd.append(args["target"])

            logger.info(f"Executing Trivy: {' '.join(cmd)}")

            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{output_format}', delete=False) as tmp_file:
                output_file = tmp_file.name

            # 重定向输出
            cmd.extend(["--output", output_file])

            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.workspace_dir or os.getcwd()
            )

            # 设置超时
            timeout = args.get("timeout", context.timeout)
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                execution_time = time.time() - start_time
                return self.create_error_result(
                    tool_name=self.name,
                    error=f"Trivy execution timed out after {timeout} seconds",
                    execution_time=execution_time
                )

            execution_time = time.time() - start_time

            # 读取输出文件
            output_content = None
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        output_content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read output file: {str(e)}")

            # 清理临时文件
            try:
                os.unlink(output_file)
            except Exception:
                pass

            # 检查执行结果
            if process.returncode != 0 and process.returncode not in [0, 1]:  # Trivy 返回 1 表示发现漏洞
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                logger.error(f"Trivy execution failed: {error_msg}")
                return self.create_error_result(
                    tool_name=self.name,
                    error=error_msg,
                    execution_time=execution_time
                )

            # 解析结果统计
            metadata = {}
            if output_content and output_format == "json":
                try:
                    result_data = json.loads(output_content)

                    # 根据扫描类型解析不同的结果结构
                    if scan_type in ["fs", "image", "repo"]:
                        metadata = {
                            "scan_type": scan_type,
                            "target": args["target"],
                            "schema_version": result_data.get("SchemaVersion"),
                            "created_at": result_data.get("CreatedAt"),
                            "results_count": len(result_data.get("Results", [])),
                            "security_checks": security_checks
                        }

                        # 统计漏洞数量
                        vulnerability_stats = {"UNKNOWN": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
                        for result in result_data.get("Results", []):
                            for vuln in result.get("Vulnerabilities", []):
                                severity = vuln.get("Severity", "UNKNOWN")
                                if severity in vulnerability_stats:
                                    vulnerability_stats[severity] += 1

                        metadata["vulnerability_stats"] = vulnerability_stats

                    elif scan_type == "config":
                        metadata = {
                            "scan_type": "config",
                            "target": args["target"],
                            "config_results": len(result_data.get("Results", [])),
                            "checks_passed": 0,
                            "checks_failed": 0
                        }

                except Exception as e:
                    logger.warning(f"Failed to parse JSON output: {str(e)}")

            logger.info(f"Trivy execution completed in {execution_time:.2f}s")

            return self.create_success_result(
                tool_name=self.name,
                execution_time=execution_time,
                output=output_content,
                metadata=metadata
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Unexpected error in Trivy execution: {str(e)}")
            return self.create_error_result(
                tool_name=self.name,
                error=str(e),
                execution_time=execution_time
            )

    async def get_version_info(self) -> Optional[str]:
        """获取 Trivy 版本信息"""
        try:
            result = subprocess.run(
                [self.trivy_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    async def update_database(self) -> bool:
        """更新 Trivy 漏洞数据库"""
        try:
            logger.info("Updating Trivy vulnerability database...")
            process = await asyncio.create_subprocess_exec(
                self.trivy_path, "image", "--download-db",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

            if process.returncode == 0:
                logger.info("Trivy database updated successfully")
                return True
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                logger.error(f"Failed to update Trivy database: {error_msg}")
                return False

        except asyncio.TimeoutError:
            logger.error("Trivy database update timed out")
            return False
        except Exception as e:
            logger.error(f"Error updating Trivy database: {str(e)}")
            return False

    async def get_supported_scanners(self) -> List[str]:
        """获取支持的扫描器列表"""
        try:
            result = subprocess.run(
                [self.trivy_path, "image", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 解析帮助信息中的扫描器列表
                scanners = ["vuln", "misconfig", "secret", "license"]
                return scanners
            return []
        except Exception:
            return []