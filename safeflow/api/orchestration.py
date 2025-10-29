"""
编排API路由

提供工作流管理的REST API接口。
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger

from safeflow.orchestration.executor import WorkflowExecutor, get_executor
from safeflow.orchestration.models import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowStatusResponse,
    WorkflowType,
    TaskStatus
)

# 创建路由
router = APIRouter(prefix="/api/orchestration", tags=["编排"])

# 全局执行器
executor: Optional[WorkflowExecutor] = None


def get_workflow_executor() -> WorkflowExecutor:
    """获取执行器实例"""
    global executor
    if executor is None:
        executor = get_executor()
    return executor


@router.post("/workflows", response_model=WorkflowExecutionResponse)
async def create_workflow(request: WorkflowExecutionRequest):
    """
    创建并启动工作流
    
    创建一个新的工作流并立即开始执行。
    """
    try:
        executor = get_workflow_executor()
        response = await executor.execute(request)
        return response
    except Exception as e:
        logger.error(f"创建工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """
    获取工作流状态
    
    查询指定工作流的当前状态、进度和结果。
    """
    try:
        executor = get_workflow_executor()
        status = await executor.get_status(workflow_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/detail")
async def get_workflow_detail(workflow_id: str):
    """
    获取工作流完整详情（用于详情页面）
    
    返回包含完整快照数据的工作流信息。
    """
    try:
        executor = get_workflow_executor()
        
        # 确保存储已初始化
        if not executor.storage._initialized:
            await executor.storage.initialize()
        
        # 从数据库获取完整数据
        workflow_data = await executor.storage.get_workflow(workflow_id)
        
        if not workflow_data:
            raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")
        
        # 返回原始数据（已经是字典格式）
        return workflow_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """
    暂停工作流
    
    暂停正在执行的工作流（用于人工审查）。
    """
    try:
        executor = get_workflow_executor()
        success = await executor.pause(workflow_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="无法暂停工作流")
        
        return {"message": "工作流已暂停", "workflow_id": workflow_id}
    except Exception as e:
        logger.error(f"暂停工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/resume", response_model=WorkflowExecutionResponse)
async def resume_workflow(workflow_id: str, checkpoint_id: Optional[str] = None):
    """
    恢复工作流
    
    从暂停状态或指定checkpoint恢复工作流执行。
    """
    try:
        executor = get_workflow_executor()
        response = await executor.resume(workflow_id, checkpoint_id)
        return response
    except Exception as e:
        logger.error(f"恢复工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """
    删除工作流
    
    删除指定的工作流及其相关数据（检查点、任务执行记录等）。
    """
    try:
        executor = get_workflow_executor()
        success = await executor.delete(workflow_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"工作流不存在或删除失败: {workflow_id}")
        
        return {"success": True, "message": f"工作流已删除: {workflow_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    """
    取消工作流
    
    取消正在执行的工作流。
    """
    try:
        executor = get_workflow_executor()
        success = await executor.cancel(workflow_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="无法取消工作流")
        
        return {"message": "工作流已取消", "workflow_id": workflow_id}
    except Exception as e:
        logger.error(f"取消工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/checkpoints")
async def list_checkpoints(workflow_id: str):
    """
    列出所有checkpoint
    
    获取指定工作流的所有checkpoint列表。
    """
    try:
        executor = get_workflow_executor()
        checkpoints = await executor.list_checkpoints(workflow_id)
        return {"workflow_id": workflow_id, "checkpoints": checkpoints}
    except Exception as e:
        logger.error(f"列出checkpoint失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_workflows(
    status: Optional[str] = None,
    workflow_type: Optional[str] = None,
    page: int = 1,
    size: int = 50
):
    """
    查询工作流列表
    
    支持按状态、类型等条件筛选。
    """
    try:
        executor = get_workflow_executor()
        
        # 转换参数
        status_filter = TaskStatus(status) if status else None
        type_filter = WorkflowType(workflow_type) if workflow_type else None
        
        offset = (page - 1) * size
        
        workflows = await executor.list_workflows(
            status=status_filter,
            workflow_type=type_filter,
            limit=size,
            offset=offset
        )
        
        return {
            "total": len(workflows),
            "page": page,
            "size": size,
            "workflows": workflows
        }
    except Exception as e:
        logger.error(f"查询工作流列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates():
    """
    列出所有工作流模板
    
    获取所有可用的工作流模板及其配置。
    """
    try:
        executor = get_workflow_executor()
        templates = executor.list_templates()
        return {"templates": templates}
    except Exception as e:
        logger.error(f"列出模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/workflows/{workflow_id}/stream")
async def stream_workflow_status(websocket: WebSocket, workflow_id: str):
    """
    实时推送工作流状态（WebSocket）
    
    通过WebSocket连接实时推送工作流的状态更新。
    """
    await websocket.accept()
    
    try:
        executor = get_workflow_executor()
        
        # 持续推送状态（简化版本，实际应该有更好的机制）
        import asyncio
        
        while True:
            try:
                status = await executor.get_status(workflow_id)
                await websocket.send_json({
                    "workflow_id": workflow_id,
                    "status": status.status.value,
                    "progress": status.progress,
                    "current_node": status.current_node,
                    "total_vulnerabilities": status.total_vulnerabilities
                })
                
                # 如果已完成，关闭连接
                if status.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    break
                
                # 等待一段时间再更新
                await asyncio.sleep(2)
                
            except ValueError:
                await websocket.send_json({"error": "工作流不存在"})
                break
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket 连接已断开: {workflow_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

