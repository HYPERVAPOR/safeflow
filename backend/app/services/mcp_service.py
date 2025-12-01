"""
MCP 服务集成
将 MCP 服务器集成到 FastAPI 应用中
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.services.mcp_server import mcp_server

logger = logging.getLogger(__name__)


class ToolExecutionRequest(BaseModel):
    """工具执行请求"""

    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="执行参数")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    workspace_dir: Optional[str] = Field(None, description="工作目录")
    timeout: int = Field(300, description="超时时间(秒)")
    enable_network: bool = Field(False, description="是否允许网络访问")


class ToolExecutionResponse(BaseModel):
    """工具执行响应"""

    success: bool = Field(..., description="是否成功")
    tool_name: str = Field(..., description="工具名称")
    execution_time: float = Field(..., description="执行时间(秒)")
    output: Optional[str] = Field(None, description="输出内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    error: Optional[str] = Field(None, description="错误信息")


class MCPService:
    """MCP 服务类"""

    def __init__(self):
        self.initialized = False

    async def initialize(self) -> bool:
        """初始化 MCP 服务"""
        if not self.initialized:
            self.initialized = await mcp_server.initialize()
        return self.initialized

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        if not await self.initialize():
            raise HTTPException(
                status_code=500, detail="Failed to initialize MCP service"
            )

        try:
            tools = []
            for tool_name, tool_instance in mcp_server.tools.items():
                tool_info = tool_instance.get_tool_info()
                tools.append(tool_info)

            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to list tools: {str(e)}"
            )

    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取指定工具的详细信息"""
        if not await self.initialize():
            raise HTTPException(
                status_code=500, detail="Failed to initialize MCP service"
            )

        if tool_name not in mcp_server.tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        try:
            tool_instance = mcp_server.tools[tool_name]
            tool_info = tool_instance.get_tool_info()

            # 添加可用性检查
            availability = await tool_instance.check_availability()
            tool_info["available"] = availability

            # 添加版本信息
            try:
                version_info = await tool_instance.get_version_info()
                if version_info:
                    tool_info["version_info"] = version_info
            except Exception as e:
                logger.warning(
                    f"Failed to get version info for '{tool_name}': {str(e)}"
                )

            return tool_info
        except Exception as e:
            logger.error(f"Error getting tool info for '{tool_name}': {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get tool info: {str(e)}"
            )

    async def execute_tool(
        self, request: ToolExecutionRequest
    ) -> ToolExecutionResponse:
        """执行指定工具"""
        if not await self.initialize():
            raise HTTPException(
                status_code=500, detail="Failed to initialize MCP service"
            )

        if request.tool_name not in mcp_server.tools:
            raise HTTPException(
                status_code=404, detail=f"Tool '{request.tool_name}' not found"
            )

        tool_instance = mcp_server.tools[request.tool_name]

        # 创建执行上下文
        from app.core.mcp_base import ExecutionContext

        context = ExecutionContext(
            user_id=request.user_id,
            session_id=request.session_id,
            request_id=f"req_{int(asyncio.get_event_loop().time())}",
            workspace_dir=request.workspace_dir,
            timeout=request.timeout,
            enable_network=request.enable_network,
            sandbox=True,
        )

        try:
            # 检查工具可用性
            if not await tool_instance.check_availability():
                raise HTTPException(
                    status_code=503,
                    detail=f"Tool '{request.tool_name}' is not available",
                )

            # 验证参数
            if not await tool_instance.validate_args(request.arguments):
                raise HTTPException(
                    status_code=400, detail="Invalid arguments for tool execution"
                )

            # 执行工具
            import time

            start_time = time.time()

            result = await tool_instance.execute(request.arguments, context)

            execution_time = time.time() - start_time

            # 构建响应
            response = ToolExecutionResponse(
                success=result.success,
                tool_name=result.tool_name,
                execution_time=execution_time,
                output=result.output,
                metadata=result.metadata,
                error=result.error,
            )

            if not result.success:
                raise HTTPException(
                    status_code=500, detail=f"Tool execution failed: {result.error}"
                )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error executing tool '{request.tool_name}': {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during tool execution: {str(e)}",
            )

    async def get_server_status(self) -> Dict[str, Any]:
        """获取服务器状态"""
        try:
            await self.initialize()

            server_info = mcp_server.get_server_info()
            tool_status = mcp_server.get_tool_status()

            # 统计可用工具数量
            available_count = sum(
                1 for status in tool_status.values() if status.get("available", False)
            )

            return {
                **server_info,
                "initialized": self.initialized,
                "available_tools_count": available_count,
                "total_tools_count": len(tool_status),
                "tools": tool_status,
            }
        except Exception as e:
            logger.error(f"Error getting server status: {str(e)}")
            return {
                "initialized": False,
                "error": str(e),
                "available_tools_count": 0,
                "total_tools_count": 0,
            }

    async def validate_tool_args(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> bool:
        """验证工具参数"""
        if not await self.initialize():
            return False

        if tool_name not in mcp_server.tools:
            return False

        tool_instance = mcp_server.tools[tool_name]
        return await tool_instance.validate_args(arguments)

    async def get_tool_categories(self) -> Dict[str, List[str]]:
        """获取按分类组织的工具列表"""
        if not await self.initialize():
            raise HTTPException(
                status_code=500, detail="Failed to initialize MCP service"
            )

        categories = {}
        for tool_name, tool_instance in mcp_server.tools.items():
            category = tool_instance.capability.category.value
            if category not in categories:
                categories[category] = []
            categories[category].append(tool_name)

        return categories

    async def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """搜索工具"""
        if not await self.initialize():
            raise HTTPException(
                status_code=500, detail="Failed to initialize MCP service"
            )

        results = []
        query_lower = query.lower()

        for tool_name, tool_instance in mcp_server.tools.items():
            tool_info = tool_instance.get_tool_info()

            # 搜索工具名称、描述、标签
            capability = tool_info.get("capability", {})
            tags = capability.get("tags", [])
            searchable_text = " ".join(
                [
                    tool_name.lower(),
                    tool_info.get("description", "").lower(),
                    " ".join(tags).lower(),
                ]
            )

            if query_lower in searchable_text:
                # 添加可用性检查
                availability = await tool_instance.check_availability()
                tool_info["available"] = availability
                results.append(tool_info)

        return results

    async def get_recommended_tools(
        self, project_type: str, languages: List[str]
    ) -> List[Dict[str, Any]]:
        """获取推荐工具"""
        if not await self.initialize():
            raise HTTPException(
                status_code=500, detail="Failed to initialize MCP service"
            )

        recommendations = []

        for tool_name, tool_instance in mcp_server.tools.items():
            capability = tool_instance.capability
            tool_info = tool_instance.get_tool_info()

            # 检查语言支持
            language_match = any(
                lang in capability.supported_languages for lang in languages
            )

            # 检查项目类型匹配
            category_match = False
            if project_type == "web_application" and capability.category.value in [
                "web_security",
                "static_analysis",
            ]:
                category_match = True
            elif project_type == "container" and capability.category.value in [
                "dependency_analysis"
            ]:
                category_match = True
            elif project_type == "api" and capability.category.value in [
                "web_security",
                "static_analysis",
            ]:
                category_match = True
            elif (
                project_type == "mobile"
                and capability.category.value == "static_analysis"
            ):
                category_match = True
            else:
                category_match = True  # 默认推荐

            if language_match or category_match:
                # 添加可用性检查
                availability = await tool_instance.check_availability()
                if availability:
                    tool_info["available"] = availability
                    tool_info["recommendation_reason"] = []
                    if language_match:
                        tool_info["recommendation_reason"].append(
                            f"Supports language: {', '.join([lang for lang in languages if lang in capability.supported_languages])}"
                        )
                    if category_match:
                        tool_info["recommendation_reason"].append(
                            f"Suitable for {project_type}"
                        )

                    recommendations.append(tool_info)

        return recommendations


# 创建全局服务实例
mcp_service = MCPService()
