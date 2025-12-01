from fastapi import APIRouter

# 导入各个模块的路由
from app.api.v1 import mcp

api_router = APIRouter()

# 注册 MCP 工具管理路由
api_router.include_router(mcp.router, tags=["MCP Tools"])


@api_router.get("/")
async def api_root():
    """API 根路径，显示可用端点"""
    return {
        "message": "SafeFlow Backend API",
        "version": "1.0.0",
        "endpoints": {
            "mcp": "/mcp/ - MCP 工具管理",
            "tools": "/tools/ - 工具管理 (已迁移到 MCP)",
            "tasks": "/tasks/ - 任务管理 (开发中)",
            "health": "/health - 健康检查",
            "docs": "/api/docs - API 文档",
        },
    }


@api_router.get("/tools")
async def get_tools_legacy():
    """获取所有注册的工具列表 (Legacy API)"""
    try:
        from app.services.mcp_service import mcp_service

        await mcp_service.initialize()
        tools = await mcp_service.list_tools()
        return {
            "tools": tools,
            "count": len(tools),
            "message": "Legacy Tools API - 推荐使用 /mcp/tools",
        }
    except Exception as e:
        return {
            "tools": [],
            "count": 0,
            "error": str(e),
            "message": "Tools endpoint error - 推荐使用 /mcp/tools",
        }


@api_router.post("/tasks")
async def create_task():
    """创建新的测试任务"""
    return {"task_id": "placeholder", "message": "Task creation endpoint - 待实现"}


@api_router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """获取指定任务详情"""
    return {"task_id": task_id, "message": "Task details endpoint - 待实现"}


@api_router.get("/mcp-migration")
async def mcp_migration_info():
    """MCP 迁移信息"""
    return {
        "title": "SafeFlow MCP 工具管理",
        "description": "我们已经将工具管理迁移到 MCP (Model Context Protocol) 架构",
        "new_endpoints": {
            "list_tools": "/mcp/tools - 列出所有工具",
            "tool_info": "/mcp/tools/{tool_name} - 获取工具详细信息",
            "execute_tool": "/mcp/tools/{tool_name}/execute - 执行工具",
            "search_tools": "/mcp/search?q=keyword - 搜索工具",
            "recommendations": "/mcp/recommendations - 获取推荐工具",
            "categories": "/mcp/categories - 获取工具分类",
            "status": "/mcp/status - 获取服务状态",
        },
        "available_tools": [
            "semgrep - 静态代码分析",
            "trivy - 漏洞扫描",
            "owasp_zap - Web 应用安全测试",
        ],
        "benefits": [
            "统一的工具接口",
            "详细的参数验证",
            "丰富的元数据",
            "标准化的输出格式",
            "更好的错误处理",
            "LLM 友好的工具描述",
        ],
        "migration_status": "completed",
    }
