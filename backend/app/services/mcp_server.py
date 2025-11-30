"""
SafeFlow MCP 服务器实现
统一的 MCP 协议服务器，管理所有安全工具
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import time

from mcp.server import Server
from mcp.types import (
    Tool, TextContent, CallToolRequest, CallToolResult,
    ListToolsRequest, ListToolsResult
)

from app.core.mcp_base import tool_registry, ExecutionContext, ExecutionResult
from app.mcp_tools.semgrep_tool import SemgrepMCPTool
from app.mcp_tools.trivy_tool import TrivyMCPTool
from app.mcp_tools.zap_tool import ZAPMCPTool

logger = logging.getLogger(__name__)


class SafeFlowMCPServer:
    """SafeFlow MCP 服务器"""

    def __init__(self):
        self.server = Server("safeflow-mcp-server")
        self.tools = {}
        self._setup_server()
        self._register_tools()

    def _setup_server(self):
        """设置 MCP 服务器"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """列出所有可用工具"""
            tools = []

            for tool_name, tool_instance in self.tools.items():
                tool_info = tool_instance.get_tool_info()

                # 转换为 MCP Tool 格式
                mcp_tool = Tool(
                    name=tool_info["name"],
                    description=tool_info["description"],
                    inputSchema=tool_info["inputSchema"]
                )
                tools.append(mcp_tool)

            logger.info(f"Listed {len(tools)} tools")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """调用指定工具"""
            if name not in self.tools:
                error_msg = f"Tool '{name}' not found. Available tools: {list(self.tools.keys())}"
                logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )

            tool_instance = self.tools[name]

            # 创建执行上下文
            context = ExecutionContext(
                user_id=arguments.get("_user_id"),
                session_id=arguments.get("_session_id"),
                request_id=arguments.get("_request_id"),
                workspace_dir=arguments.get("_workspace_dir"),
                timeout=arguments.get("_timeout", 300),
                max_memory=arguments.get("_max_memory", "1GB"),
                enable_network=arguments.get("_enable_network", False),
                sandbox=arguments.get("_sandbox", True)
            )

            # 移除内部参数
            clean_args = {k: v for k, v in arguments.items() if not k.startswith("_")}

            try:
                logger.info(f"Executing tool '{name}' with args: {list(clean_args.keys())}")

                # 准备执行
                if not await tool_instance.prepare_execution(clean_args, context):
                    error_msg = f"Failed to prepare execution for tool '{name}'"
                    logger.error(error_msg)
                    return CallToolResult(
                        content=[TextContent(type="text", text=error_msg)],
                        isError=True
                    )

                # 执行工具
                start_time = time.time()
                result = await tool_instance.execute(clean_args, context)
                execution_time = time.time() - start_time

                # 构建响应
                if result.success:
                    response_text = f"✅ Tool '{name}' executed successfully\n\n"
                    response_text += f"Execution time: {execution_time:.2f} seconds\n"

                    if result.metadata:
                        response_text += f"Metadata: {json.dumps(result.metadata, indent=2)}\n\n"

                    if result.output:
                        response_text += "Output:\n"
                        response_text += result.output
                    elif result.output_file:
                        response_text += f"Results saved to: {result.output_file}"
                    else:
                        response_text += "Tool completed successfully (no output)"

                    logger.info(f"Tool '{name}' executed successfully in {execution_time:.2f}s")

                    return CallToolResult(
                        content=[TextContent(type="text", text=response_text)],
                        isError=False
                    )
                else:
                    response_text = f"❌ Tool '{name}' execution failed\n\n"
                    response_text += f"Execution time: {execution_time:.2f} seconds\n"
                    response_text += f"Error: {result.error}\n"

                    if result.metadata:
                        response_text += f"Metadata: {json.dumps(result.metadata, indent=2)}\n"

                    logger.error(f"Tool '{name}' failed: {result.error}")

                    return CallToolResult(
                        content=[TextContent(type="text", text=response_text)],
                        isError=True
                    )

            except Exception as e:
                error_msg = f"Unexpected error executing tool '{name}': {str(e)}"
                logger.error(error_msg, exc_info=True)

                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )

    def _register_tools(self):
        """注册所有工具"""

        # 注册 Semgrep
        try:
            semgrep_tool = SemgrepMCPTool()
            self.tools[semgrep_tool.name] = semgrep_tool
            tool_registry.register(semgrep_tool)
            logger.info(f"Registered Semgrep tool: {semgrep_tool.name}")
        except Exception as e:
            logger.error(f"Failed to register Semgrep tool: {str(e)}")

        # 注册 Trivy
        try:
            trivy_tool = TrivyMCPTool()
            self.tools[trivy_tool.name] = trivy_tool
            tool_registry.register(trivy_tool)
            logger.info(f"Registered Trivy tool: {trivy_tool.name}")
        except Exception as e:
            logger.error(f"Failed to register Trivy tool: {str(e)}")

        # 注册 OWASP ZAP
        try:
            zap_tool = ZAPMCPTool()
            self.tools[zap_tool.name] = zap_tool
            tool_registry.register(zap_tool)
            logger.info(f"Registered ZAP tool: {zap_tool.name}")
        except Exception as e:
            logger.error(f"Failed to register ZAP tool: {str(e)}")

        logger.info(f"Total registered tools: {len(self.tools)}")

    async def initialize(self) -> bool:
        """初始化服务器"""
        try:
            logger.info("Initializing SafeFlow MCP Server...")

            # 检查所有工具的可用性
            available_tools = []
            unavailable_tools = []

            for tool_name, tool_instance in self.tools.items():
                try:
                    if await tool_instance.check_availability():
                        available_tools.append(tool_name)
                        logger.info(f"Tool '{tool_name}' is available")
                    else:
                        unavailable_tools.append(tool_name)
                        logger.warning(f"Tool '{tool_name}' is not available")
                except Exception as e:
                    unavailable_tools.append(tool_name)
                    logger.error(f"Error checking availability of tool '{tool_name}': {str(e)}")

            logger.info(f"Server initialization completed")
            logger.info(f"Available tools: {available_tools}")
            logger.info(f"Unavailable tools: {unavailable_tools}")

            return len(available_tools) > 0

        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {str(e)}", exc_info=True)
            return False

    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "name": "SafeFlow MCP Server",
            "version": "1.0.0",
            "description": "MCP server for SafeFlow security testing platform",
            "tools_count": len(self.tools),
            "tools": list(self.tools.keys())
        }

    def get_tool_status(self) -> Dict[str, Any]:
        """获取所有工具的状态"""
        status = {}

        for tool_name, tool_instance in self.tools.items():
            try:
                capability = tool_instance.capability
                status[tool_name] = {
                    "available": True,  # 简化检查，实际需要异步检查
                    "category": capability.category.value,
                    "version": capability.version,
                    "description": capability.description,
                    "supported_languages": capability.supported_languages,
                    "output_formats": capability.output_formats
                }
            except Exception as e:
                status[tool_name] = {
                    "available": False,
                    "error": str(e)
                }

        return status

    async def shutdown(self):
        """关闭服务器"""
        logger.info("Shutting down SafeFlow MCP Server...")

        # 清理工具资源
        for tool_name, tool_instance in self.tools.items():
            try:
                if hasattr(tool_instance, 'cleanup'):
                    await tool_instance.cleanup()
                logger.info(f"Cleaned up tool '{tool_name}'")
            except Exception as e:
                logger.error(f"Error cleaning up tool '{tool_name}': {str(e)}")

        logger.info("MCP server shutdown completed")


# 创建全局服务器实例
mcp_server = SafeFlowMCPServer()


async def get_mcp_server() -> SafeFlowMCPServer:
    """获取 MCP 服务器实例"""
    await mcp_server.initialize()
    return mcp_server


# 用于独立运行的函数
async def run_server():
    """独立运行 MCP 服务器"""
    server = await get_mcp_server()

    try:
        # 这里需要根据 MCP SDK 的实际 API 来运行服务器
        # 示例代码，需要根据实际 SDK 调整
        logger.info("Starting SafeFlow MCP Server...")

        # 模拟服务器运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
    finally:
        await server.shutdown()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 运行服务器
    asyncio.run(run_server())