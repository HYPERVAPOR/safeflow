"""
MCP 工具管理 API 端点
提供工具注册、发现、执行等 REST API 接口
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends, Body
from fastapi.responses import JSONResponse

from app.services.mcp_service import (
    mcp_service, ToolExecutionRequest, ToolExecutionResponse
)
from app.core.mcp_base import ToolCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP Tools"])


@router.get("/status", summary="获取 MCP 服务状态")
async def get_mcp_status():
    """
    获取 MCP 服务器状态和所有工具的可用性信息

    Returns:
        MCP 服务状态信息，包括可用工具数量和详细信息
    """
    try:
        status = await mcp_service.get_server_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting MCP status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get MCP status: {str(e)}")


@router.get("/tools", summary="列出所有可用工具")
async def list_tools(
    category: Optional[str] = Query(None, description="按分类过滤工具"),
    available_only: bool = Query(True, description="仅显示可用工具")
):
    """
    获取所有已注册的 MCP 工具列表

    Args:
        category: 可选的分类过滤器 (static_analysis, dynamic_analysis, dependency_analysis, web_security, fuzzing)
        available_only: 是否只显示可用工具

    Returns:
        工具列表，包含每个工具的详细信息
    """
    try:
        tools = await mcp_service.list_tools()

        # 过滤结果
        filtered_tools = []
        for tool in tools:
            # 检查可用性
            if available_only and not tool.get("available", True):
                continue

            # 检查分类
            if category and tool.get("capability", {}).get("category") != category:
                continue

            filtered_tools.append(tool)

        return JSONResponse(content={
            "tools": filtered_tools,
            "total_count": len(filtered_tools),
            "category_filter": category,
            "available_only": available_only
        })

    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.get("/tools/{tool_name}", summary="获取指定工具的详细信息")
async def get_tool_info(tool_name: str):
    """
    获取指定工具的详细信息和配置选项

    Args:
        tool_name: 工具名称

    Returns:
        工具详细信息，包括参数、能力描述、版本信息等
    """
    try:
        tool_info = await mcp_service.get_tool_info(tool_name)
        return JSONResponse(content=tool_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool info for '{tool_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tool info: {str(e)}")


@router.post("/tools/{tool_name}/execute", summary="执行指定工具")
async def execute_tool(
    tool_name: str,
    request: ToolExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    执行指定的安全工具

    Args:
        tool_name: 工具名称
        request: 执行请求，包含参数和配置

    Returns:
        执行结果，包含输出、元数据和执行时间
    """
    try:
        # 验证工具名称
        if tool_name != request.tool_name:
            raise HTTPException(
                status_code=400,
                detail=f"Tool name mismatch: URL parameter '{tool_name}' vs request body '{request.tool_name}'"
            )

        # 执行工具
        result = await mcp_service.execute_tool(request)

        return JSONResponse(content=result.dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during tool execution: {str(e)}"
        )


@router.post("/tools/{tool_name}/validate", summary="验证工具参数")
async def validate_tool_arguments(
    tool_name: str,
    arguments: dict = Body(...)
):
    """
    验证指定工具的参数是否正确

    Args:
        tool_name: 工具名称
        arguments: 要验证的参数

    Returns:
        验证结果
    """
    try:
        is_valid = await mcp_service.validate_tool_args(tool_name, arguments)
        return JSONResponse(content={
            "tool_name": tool_name,
            "valid": is_valid,
            "arguments": arguments
        })
    except Exception as e:
        logger.error(f"Error validating arguments for tool '{tool_name}': {str(e)}")
        return JSONResponse(
            content={
                "tool_name": tool_name,
                "valid": False,
                "error": str(e),
                "arguments": arguments
            },
            status_code=400
        )


@router.get("/categories", summary="获取工具分类")
async def get_tool_categories():
    """
    获取按分类组织的工具列表

    Returns:
        分类字典，包含每个分类下的工具列表
    """
    try:
        categories = await mcp_service.get_tool_categories()
        return JSONResponse(content=categories)
    except Exception as e:
        logger.error(f"Error getting tool categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tool categories: {str(e)}")


@router.get("/search", summary="搜索工具")
async def search_tools(
    q: str = Query(..., min_length=2, description="搜索关键词"),
    available_only: bool = Query(True, description="仅搜索可用工具")
):
    """
    根据关键词搜索工具

    Args:
        q: 搜索关键词，会搜索工具名称、描述、标签
        available_only: 是否只搜索可用工具

    Returns:
        匹配的工具列表
    """
    try:
        results = await mcp_service.search_tools(q)

        # 过滤可用性
        if available_only:
            results = [tool for tool in results if tool.get("available", True)]

        return JSONResponse(content={
            "query": q,
            "results": results,
            "count": len(results),
            "available_only": available_only
        })

    except Exception as e:
        logger.error(f"Error searching tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search tools: {str(e)}")


@router.post("/recommendations", summary="获取工具推荐")
async def get_tool_recommendations(
    project_type: str = Query(..., description="项目类型"),
    languages: List[str] = Query(..., description="项目使用的编程语言列表")
):
    """
    根据项目类型和编程语言获取工具推荐

    Args:
        project_type: 项目类型 (web_application, container, api, mobile, desktop)
        languages: 使用的编程语言列表

    Returns:
        推荐的工具列表和推荐原因
    """
    try:
        recommendations = await mcp_service.get_recommended_tools(project_type, languages)
        return JSONResponse(content={
            "project_type": project_type,
            "languages": languages,
            "recommendations": recommendations,
            "count": len(recommendations)
        })

    except Exception as e:
        logger.error(f"Error getting tool recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/capabilities", summary="获取 MCP 服务能力")
async def get_mcp_capabilities():
    """
    获取 MCP 服务的能力信息

    Returns:
        服务能力信息，包括支持的操作、工具类型等
    """
    try:
        status = await mcp_service.get_server_status()

        capabilities = {
            "mcp_version": "1.0",
            "server_name": "SafeFlow MCP Server",
            "supported_operations": [
                "list_tools",
                "get_tool_info",
                "execute_tool",
                "validate_arguments",
                "search_tools",
                "get_recommendations"
            ],
            "supported_categories": [category.value for category in ToolCategory],
            "authentication": "none",  # 目前不需要认证
            "rate_limiting": {
                "enabled": False,
                "requests_per_minute": None
            },
            "concurrent_executions": True,
            "sandbox_execution": True,
            "file_upload_support": False,
            "streaming_output": False
        }

        return JSONResponse(content={
            "capabilities": capabilities,
            "server_info": {
                "name": status.get("name"),
                "version": status.get("version"),
                "tools_count": status.get("tools_count"),
                "available_tools_count": status.get("available_tools_count")
            }
        })

    except Exception as e:
        logger.error(f"Error getting MCP capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.post("/initialize", summary="初始化 MCP 服务")
async def initialize_mcp_service():
    """
    手动初始化 MCP 服务

    Returns:
        初始化结果
    """
    try:
        success = await mcp_service.initialize()
        return JSONResponse(content={
            "success": success,
            "message": "MCP service initialized successfully" if success else "MCP service initialization failed"
        })
    except Exception as e:
        logger.error(f"Error initializing MCP service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize MCP service: {str(e)}")






async def _get_available_tool_names() -> List[str]:
    """获取可用工具名称列表"""
    try:
        tools = await mcp_service.list_tools()
        return [tool["name"] for tool in tools if tool.get("available", True)]
    except Exception:
        return []