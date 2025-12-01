"""
OWASP ZAP MCP 工具实现
Web 应用安全测试工具的 MCP 封装
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional

import aiohttp

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


class ZAPMCPTool(MCPToolBase):
    """OWASP ZAP Web 应用安全测试工具"""

    def __init__(self):
        super().__init__()
        self.name = "owasp_zap"
        self.zap_path = self._find_zap_path()
        self.zap_host = "127.0.0.1"
        self.zap_port = 8080
        self.zap_api_key = None
        self.zap_process = None

    def _find_zap_path(self) -> Optional[str]:
        """查找 ZAP 可执行文件路径"""
        # 检查常见路径
        paths = [
            "zap",  # PATH 中
            "zap.sh",  # 脚本名称
            os.path.expanduser("~/bin/ZAP_2.16.1/zap.sh"),  # 用户安装
            "/opt/zap/zap.sh",  # 系统安装
            "/Applications/ZAP.app/Contents/MacOS/zap.sh",  # macOS
        ]

        for path in paths:
            full_path = os.path.expanduser(path)
            if os.path.exists(full_path):
                return full_path

        # 检查 Docker
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return "docker"  # 标识使用 Docker
        except Exception:
            pass

        return None

    @property
    def parameters(self) -> List[ToolParameter]:
        """获取 ZAP 参数定义"""
        return [
            ToolParameter(
                name="target_url",
                type=ParameterType.STRING,
                description="目标 Web 应用 URL",
                required=True,
                pattern=r"^https?://.+",
                min_length=1,
                max_length=1000,
                format="url",
            ),
            ToolParameter(
                name="scan_type",
                type=ParameterType.STRING,
                description="扫描类型",
                required=False,
                default="quick",
                enum=["quick", "active", "passive", "spider", "ajaxspider", "api"],
            ),
            ToolParameter(
                name="auth_type",
                type=ParameterType.STRING,
                description="认证类型",
                required=False,
                default="none",
                enum=[
                    "none",
                    "basic",
                    "form",
                    "digest",
                    "ntlm",
                    "cookie",
                    "jwt",
                    "oauth",
                ],
            ),
            ToolParameter(
                name="username",
                type=ParameterType.STRING,
                description="用户名（用于认证）",
                required=False,
                default="",
                max_length=100,
            ),
            ToolParameter(
                name="password",
                type=ParameterType.STRING,
                description="密码（用于认证）",
                required=False,
                default="",
                max_length=200,
                format="sensitive",
            ),
            ToolParameter(
                name="auth_login_url",
                type=ParameterType.STRING,
                description="登录页面 URL（表单认证）",
                required=False,
                default="",
                format="url",
            ),
            ToolParameter(
                name="auth_username_field",
                type=ParameterType.STRING,
                description="用户名字段名称（表单认证）",
                required=False,
                default="username",
                max_length=50,
            ),
            ToolParameter(
                name="auth_password_field",
                type=ParameterType.STRING,
                description="密码字段名称（表单认证）",
                required=False,
                default="password",
                max_length=50,
            ),
            ToolParameter(
                name="include_urls",
                type=ParameterType.ARRAY,
                description="要包含的 URL 模式列表",
                required=False,
                default=[],
            ),
            ToolParameter(
                name="exclude_urls",
                type=ParameterType.ARRAY,
                description="要排除的 URL 模式列表",
                required=False,
                default=[".*\\.(css|js|png|jpg|jpeg|gif|ico|woff|woff2)$"],
            ),
            ToolParameter(
                name="max_depth",
                type=ParameterType.INTEGER,
                description="最大爬取深度",
                required=False,
                default=5,
                minimum=1,
                maximum=10,
            ),
            ToolParameter(
                name="max_children",
                type=ParameterType.INTEGER,
                description="每个节点的最大子节点数",
                required=False,
                default=10,
                minimum=1,
                maximum=100,
            ),
            ToolParameter(
                name="attack_strength",
                type=ParameterType.STRING,
                description="攻击强度",
                required=False,
                default="MEDIUM",
                enum=["LOW", "MEDIUM", "HIGH", "INSIGHT"],
            ),
            ToolParameter(
                name="alert_threshold",
                type=ParameterType.STRING,
                description="告警阈值",
                required=False,
                default="MEDIUM",
                enum=["LOW", "MEDIUM", "HIGH"],
            ),
            ToolParameter(
                name="output_format",
                type=ParameterType.STRING,
                description="输出格式",
                required=False,
                default="json",
                enum=["json", "html", "xml", "md"],
            ),
            ToolParameter(
                name="timeout",
                type=ParameterType.INTEGER,
                description="扫描超时时间(秒)",
                required=False,
                default=600,
                minimum=60,
                maximum=3600,
            ),
            ToolParameter(
                name="delay_in_seconds",
                type=ParameterType.INTEGER,
                description="请求间隔延迟(秒)",
                required=False,
                default=0,
                minimum=0,
                maximum=60,
            ),
            ToolParameter(
                name="context_name",
                type=ParameterType.STRING,
                description="上下文名称",
                required=False,
                default="Default Context",
                max_length=100,
            ),
            ToolParameter(
                name="use_ajax_spider",
                type=ParameterType.BOOLEAN,
                description="是否使用 AJAX Spider",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="enable_api_scan",
                type=ParameterType.BOOLEAN,
                description="是否启用 API 扫描",
                required=False,
                default=False,
            ),
        ]

    @property
    def capability(self) -> ToolCapability:
        """获取 ZAP 能力描述"""
        return ToolCapability(
            category=ToolCategory.WEB_SECURITY,
            description=(
                "OWASP ZAP (Zed Attack Proxy) 是一个开源的 Web 应用安全测试工具，"
                "用于自动发现 Web 应用中的安全漏洞。支持被动扫描、主动扫描、爬虫、"
                "暴力破解、模糊测试等多种安全测试功能。集成 OWASP Top Ten、"
                "WASC Threat Classification 等标准，能够检测 SQL 注入、XSS、CSRF、"
                "认证绕过、会话管理等常见安全漏洞。提供丰富的 API 接口，"
                "支持自动化测试和持续集成。"
            ),
            version="2.16.1",
            author="OWASP Foundation",
            homepage="https://www.zaproxy.org/",
            documentation="https://www.zaproxy.org/docs/",
            supported_languages=[
                "Web Applications",
                "REST APIs",
                "GraphQL",
                "SOAP",
                "WebSocket",
            ],
            supported_formats=[
                "web_applications",
                "rest_apis",
                "graphql_endpoints",
                "web_services",
            ],
            output_formats=["json", "html", "xml", "markdown", "sarif"],
            tags=[
                "web_security",
                "penetration_testing",
                "vulnerability_scanner",
                "owasp_top_ten",
                "dast",
                "security_testing",
                "api_security",
            ],
        )

    async def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证 ZAP 参数"""
        try:
            # 检查必需参数
            if "target_url" not in args:
                logger.error("Missing required parameter: target_url")
                return False

            target_url = args["target_url"]

            # 验证 URL 格式
            if not target_url.startswith(("http://", "https://")):
                logger.error(f"Invalid target URL format: {target_url}")
                return False

            # 验证扫描类型
            if "scan_type" in args:
                valid_scan_types = [
                    param.enum for param in self.parameters if param.name == "scan_type"
                ][0]
                if args["scan_type"] not in valid_scan_types:
                    logger.error(f"Invalid scan type: {args['scan_type']}")
                    return False

            # 验证认证类型
            if "auth_type" in args:
                auth_types = [
                    param.enum for param in self.parameters if param.name == "auth_type"
                ][0]
                if args["auth_type"] not in auth_types:
                    logger.error(f"Invalid auth type: {args['auth_type']}")
                    return False

            # 验证认证参数完整性
            auth_type = args.get("auth_type", "none")
            if auth_type != "none":
                if auth_type in ["basic", "digest", "form", "ntlm"]:
                    if not args.get("username"):
                        logger.error(f"Username required for auth type: {auth_type}")
                        return False
                    if not args.get("password"):
                        logger.error(f"Password required for auth type: {auth_type}")
                        return False

                if auth_type == "form":
                    if not args.get("auth_login_url"):
                        logger.error("Login URL required for form authentication")
                        return False

            # 验证攻击强度
            if "attack_strength" in args:
                strengths = [
                    param.enum
                    for param in self.parameters
                    if param.name == "attack_strength"
                ][0]
                if args["attack_strength"] not in strengths:
                    logger.error(f"Invalid attack strength: {args['attack_strength']}")
                    return False

            # 验证告警阈值
            if "alert_threshold" in args:
                thresholds = [
                    param.enum
                    for param in self.parameters
                    if param.name == "alert_threshold"
                ][0]
                if args["alert_threshold"] not in thresholds:
                    logger.error(f"Invalid alert threshold: {args['alert_threshold']}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating args: {str(e)}")
            return False

    async def check_availability(self) -> bool:
        """检查 ZAP 可用性"""
        try:
            # 检查 Java 环境
            try:
                result = subprocess.run(
                    ["java", "-version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    logger.error("Java not available for ZAP")
                    return False
            except Exception as e:
                logger.error(f"Java check failed: {str(e)}")
                return False

            # 检查 ZAP 安装
            if not self.zap_path:
                logger.error("ZAP not found")
                return False

            if self.zap_path == "docker":
                # 检查 Docker 中的 ZAP
                try:
                    result = subprocess.run(
                        ["docker", "run", "--rm", "owasp/zap2docker-stable", "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode != 0:
                        logger.error("ZAP Docker image not available")
                        return False
                except Exception as e:
                    logger.error(f"ZAP Docker check failed: {str(e)}")
                    return False
            else:
                # 检查本地 ZAP
                if not os.path.exists(self.zap_path):
                    logger.error(f"ZAP not found at: {self.zap_path}")
                    return False

            logger.info("ZAP is available")
            return True

        except Exception as e:
            logger.error(f"ZAP availability check failed: {str(e)}")
            return False

    async def start_zap_daemon(self) -> bool:
        """启动 ZAP 守护进程"""
        try:
            if self.zap_path == "docker":
                # 启动 Docker 版本的 ZAP
                cmd = [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    f"zap-{uuid.uuid4().hex[:8]}",
                    "-p",
                    f"{self.zap_port}:8080",
                    "owasp/zap2docker-stable",
                    "zap.sh",
                    "-daemon",
                    "-host",
                    "0.0.0.0",
                    "-port",
                    "8080",
                    "-config",
                    "api.addrs.addr.name=.*",
                    "-config",
                    "api.addrs.addr.regex=true",
                ]
            else:
                # 启动本地 ZAP
                cmd = [
                    "java",
                    "-jar",
                    os.path.join(os.path.dirname(self.zap_path), "zap-2.16.1.jar"),
                    "-daemon",
                    "-host",
                    self.zap_host,
                    "-port",
                    str(self.zap_port),
                    "-config",
                    "api.addrs.addr.name=.*",
                    "-config",
                    "api.addrs.addr.regex=true",
                ]

            logger.info(f"Starting ZAP daemon: {' '.join(cmd)}")

            self.zap_process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            # 等待 ZAP 启动
            max_wait = 30
            for i in range(max_wait):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"http://{self.zap_host}:{self.zap_port}/JSON/core/view/version/",
                            timeout=aiohttp.ClientTimeout(total=2),
                        ) as response:
                            if response.status == 200:
                                logger.info("ZAP daemon started successfully")
                                return True
                except Exception:
                    pass

                await asyncio.sleep(1)

            logger.error("ZAP daemon failed to start")
            return False

        except Exception as e:
            logger.error(f"Error starting ZAP daemon: {str(e)}")
            return False

    async def stop_zap_daemon(self):
        """停止 ZAP 守护进程"""
        if self.zap_process:
            try:
                self.zap_process.terminate()
                await self.zap_process.wait()
                logger.info("ZAP daemon stopped")
            except Exception as e:
                logger.warning(f"Error stopping ZAP daemon: {str(e)}")

    async def execute(
        self, args: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """执行 ZAP 扫描"""
        start_time = time.time()

        try:
            # 启动 ZAP 守护进程
            if not await self.start_zap_daemon():
                return self.create_error_result(
                    tool_name=self.name,
                    error="Failed to start ZAP daemon",
                    execution_time=time.time() - start_time,
                )

            try:
                # 执行扫描
                result = await self._perform_scan(args, context)
                return result
            finally:
                # 停止 ZAP 守护进程
                await self.stop_zap_daemon()

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Unexpected error in ZAP execution: {str(e)}")
            await self.stop_zap_daemon()
            return self.create_error_result(
                tool_name=self.name, error=str(e), execution_time=execution_time
            )

    async def _perform_scan(
        self, args: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """执行具体的扫描操作"""
        start_time = time.time()
        target_url = args["target_url"]
        scan_type = args.get("scan_type", "quick")

        try:
            async with aiohttp.ClientSession() as session:
                # 获取 ZAP API 密钥
                await self._get_api_key(session)

                # 配置认证
                if args.get("auth_type", "none") != "none":
                    await self._configure_auth(session, args)

                # 配置上下文
                context_id = await self._create_context(session, args)

                # 启动爬虫
                scan_id = await self._start_spider(
                    session, target_url, args, context_id
                )
                if not scan_id:
                    return self.create_error_result(
                        tool_name=self.name,
                        error="Failed to start spider",
                        execution_time=time.time() - start_time,
                    )

                # 等待爬虫完成
                await self._wait_for_spider_completion(
                    session, scan_id, args.get("timeout", context.timeout)
                )

                # 启动扫描
                if scan_type in ["quick", "active"]:
                    scan_result = await self._start_active_scan(
                        session, target_url, args, context_id
                    )
                    if scan_result:
                        await self._wait_for_scan_completion(
                            session, scan_result, args.get("timeout", context.timeout)
                        )

                # 获取结果
                results = await self._get_results(session, args)

                execution_time = time.time() - start_time
                logger.info(f"ZAP scan completed in {execution_time:.2f}s")

                metadata = {
                    "target_url": target_url,
                    "scan_type": scan_type,
                    "alerts_count": len(results.get("alerts", [])),
                    "high_risk_alerts": len(
                        [
                            a
                            for a in results.get("alerts", [])
                            if a.get("risk") in ["High", "Critical"]
                        ]
                    ),
                }

                return self.create_success_result(
                    tool_name=self.name,
                    execution_time=execution_time,
                    output=json.dumps(results, indent=2, ensure_ascii=False),
                    metadata=metadata,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in ZAP scan: {str(e)}")
            return self.create_error_result(
                tool_name=self.name, error=str(e), execution_time=execution_time
            )

    async def _get_api_key(self, session: aiohttp.ClientSession):
        """获取 ZAP API 密钥"""
        if not self.zap_api_key:
            # ZAP 默认不需要 API 密钥，使用空字符串
            self.zap_api_key = ""

    async def _configure_auth(
        self, session: aiohttp.ClientSession, args: Dict[str, Any]
    ):
        """配置认证"""
        auth_type = args.get("auth_type", "none")
        if auth_type == "none":
            return

        # 这里实现各种认证类型的配置
        # 基础认证、表单认证、JWT 等
        logger.info(f"Configuring authentication: {auth_type}")

    async def _create_context(
        self, session: aiohttp.ClientSession, args: Dict[str, Any]
    ) -> str:
        """创建扫描上下文"""
        context_name = args.get("context_name", "Default Context")

        try:
            params = {"contextName": context_name, "apiKey": self.zap_api_key}

            async with session.post(
                f"http://{self.zap_host}:{self.zap_port}/JSON/context/action/newContext/",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("contextId", "0")
                else:
                    return "0"  # 默认上下文
        except Exception as e:
            logger.warning(f"Failed to create context: {str(e)}")
            return "0"

    async def _start_spider(
        self,
        session: aiohttp.ClientSession,
        target_url: str,
        args: Dict[str, Any],
        context_id: str,
    ) -> str:
        """启动爬虫"""
        spider_type = (
            "ajaxspider"
            if args.get("use_ajax_spider", True) and args.get("scan_type") != "api"
            else "spider"
        )

        try:
            params = {
                "url": target_url,
                "maxChildren": args.get("max_children", 10),
                "recurse": "true",
                "contextName": args.get("context_name", "Default Context"),
                "apiKey": self.zap_api_key,
            }

            if spider_type == "ajaxspider":
                url = f"http://{self.zap_host}:{self.zap_port}/JSON/ajaxSpider/action/scan/"
            else:
                url = f"http://{self.zap_host}:{self.zap_port}/JSON/spider/action/scan/"
                params["maxDepth"] = args.get("max_depth", 5)

            async with session.post(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("scan", "")
                else:
                    logger.error(f"Failed to start spider: {response.status}")
                    return ""

        except Exception as e:
            logger.error(f"Error starting spider: {str(e)}")
            return ""

    async def _wait_for_spider_completion(
        self, session: aiohttp.ClientSession, scan_id: str, timeout: int
    ):
        """等待爬虫完成"""
        max_wait = timeout
        wait_time = 0

        while wait_time < max_wait:
            try:
                params = {"apiKey": self.zap_api_key}

                async with session.get(
                    f"http://{self.zap_host}:{self.zap_port}/JSON/spider/view/status/",
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = int(data.get("status", 0))
                        if status >= 100:
                            logger.info("Spider scan completed")
                            return

                await asyncio.sleep(5)
                wait_time += 5

            except Exception as e:
                logger.error(f"Error checking spider status: {str(e)}")
                break

        logger.warning(f"Spider scan timed out after {timeout} seconds")

    async def _start_active_scan(
        self,
        session: aiohttp.ClientSession,
        target_url: str,
        args: Dict[str, Any],
        context_id: str,
    ) -> str:
        """启动主动扫描"""
        try:
            params = {
                "url": target_url,
                "recurse": "true",
                "contextId": context_id,
                "policy": "Default Policy",
                "attackStrength": args.get("attack_strength", "MEDIUM"),
                "alertThreshold": args.get("alert_threshold", "MEDIUM"),
                "apiKey": self.zap_api_key,
            }

            async with session.post(
                f"http://{self.zap_host}:{self.zap_port}/JSON/ascan/action/scan/",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("scan", "")
                else:
                    logger.error(f"Failed to start active scan: {response.status}")
                    return ""

        except Exception as e:
            logger.error(f"Error starting active scan: {str(e)}")
            return ""

    async def _wait_for_scan_completion(
        self, session: aiohttp.ClientSession, scan_id: str, timeout: int
    ):
        """等待扫描完成"""
        max_wait = timeout
        wait_time = 0

        while wait_time < max_wait:
            try:

                async with session.get(
                    f"http://{self.zap_host}:{self.zap_port}/JSON/ascan/view/status/",
                    params={"scanId": scan_id, "apiKey": self.zap_api_key},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = int(data.get("status", 0))
                        if status >= 100:
                            logger.info("Active scan completed")
                            return

                await asyncio.sleep(10)
                wait_time += 10

            except Exception as e:
                logger.error(f"Error checking scan status: {str(e)}")
                break

        logger.warning(f"Active scan timed out after {timeout} seconds")

    async def _get_results(
        self, session: aiohttp.ClientSession, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取扫描结果"""
        try:
            params = {
                "baseurl": args["target_url"],
                "start": "0",
                "count": "1000",
                "apiKey": self.zap_api_key,
            }

            async with session.get(
                f"http://{self.zap_host}:{self.zap_port}/JSON/core/view/alerts/",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Failed to get results: {response.status}")
                    return {"alerts": []}

        except Exception as e:
            logger.error(f"Error getting results: {str(e)}")
            return {"alerts": []}

    async def get_version_info(self) -> Optional[str]:
        """获取 ZAP 版本信息"""
        try:
            if not await self.start_zap_daemon():
                return None

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{self.zap_host}:{self.zap_port}/JSON/core/view/version/",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get("version", "unknown")
            finally:
                await self.stop_zap_daemon()

        except Exception:
            return None
