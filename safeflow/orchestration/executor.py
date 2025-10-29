"""
工作流执行器

整合编排引擎、调度器、存储等组件，提供统一的工作流执行接口。
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
from loguru import logger

from safeflow.orchestration.engine import OrchestrationEngine
from safeflow.orchestration.scheduler import TaskScheduler
from safeflow.orchestration.storage import WorkflowStorage
from safeflow.orchestration.templates import get_template, list_templates
from safeflow.orchestration.models import (
    WorkflowState, WorkflowType, ScanTarget, TaskStatus,
    WorkflowExecutionRequest, WorkflowExecutionResponse,
    WorkflowStatusResponse
)
from safeflow.orchestration.config import WorkflowConfig, get_config_for_scenario


class WorkflowExecutor:
    """
    工作流执行器
    
    功能：
    1. 创建和执行工作流
    2. 管理工作流生命周期
    3. 持久化工作流状态
    4. 提供查询接口
    """
    
    def __init__(
        self,
        engine: Optional[OrchestrationEngine] = None,
        scheduler: Optional[TaskScheduler] = None,
        storage: Optional[WorkflowStorage] = None,
        config: Optional[WorkflowConfig] = None
    ):
        """
        初始化执行器
        
        Args:
            engine: 编排引擎
            scheduler: 任务调度器
            storage: 存储
            config: 配置
        """
        self.config = config or WorkflowConfig()
        self.engine = engine or OrchestrationEngine(self.config)
        self.scheduler = scheduler or TaskScheduler(self.config)
        self.storage = storage or WorkflowStorage(self.config.storage)
        
        logger.info("WorkflowExecutor 初始化完成")
    
    async def execute(
        self,
        request: WorkflowExecutionRequest
    ) -> WorkflowExecutionResponse:
        """
        执行工作流
        
        Args:
            request: 工作流执行请求
            
        Returns:
            工作流执行响应
        """
        logger.info(f"开始执行工作流: {request.workflow_type.value}")
        
        try:
            # 1. 获取模板
            template = get_template(request.workflow_type)
            
            # 2. 合并配置
            config = request.config or {}
            workflow_config = template.get_default_config()
            
            # 3. 创建工作流
            workflow_id = self.engine.create_workflow(
                workflow_type=request.workflow_type,
                target=request.target,
                tool_ids=request.tool_ids or template.get_required_tools(),
                custom_config=config,
                created_by=request.created_by
            )
            
            # 4. 初始化存储
            if not self.storage._initialized:
                await self.storage.initialize()
            
            # 5. 执行工作流（使用简化模式）
            final_state = self.engine.execute_workflow(workflow_id)
            
            # 6. 保存到数据库
            await self.storage.save_workflow(final_state)
            
            # 7. 生成响应
            response = WorkflowExecutionResponse(
                workflow_id=workflow_id,
                status=final_state.status,
                message=f"工作流执行{'成功' if final_state.status == TaskStatus.SUCCESS else '失败'}",
                summary=final_state.get_summary()
            )
            
            logger.success(
                f"工作流执行完成: {workflow_id}，"
                f"状态: {final_state.status.value}"
            )
            
            return response
            
        except Exception as e:
            error_msg = f"工作流执行失败: {str(e)}"
            logger.error(error_msg)
            
            return WorkflowExecutionResponse(
                workflow_id=str(uuid4()),
                status=TaskStatus.FAILED,
                message=error_msg,
                summary={"error": error_msg}
            )
    
    async def get_status(self, workflow_id: str) -> WorkflowStatusResponse:
        """
        获取工作流状态
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流状态响应
        """
        try:
            # 先从引擎内存中获取
            workflow = self.engine.get_workflow(workflow_id)
            
            if workflow:
                state = workflow["state"]
                
                # 计算进度
                total_nodes = len(state.node_results) if state.node_results else 0
                # 简单进度计算（可以根据实际情况优化）
                if state.is_completed():
                    progress = 100.0
                elif total_nodes > 0:
                    progress = (total_nodes / 5) * 100  # 假设平均5个节点
                else:
                    progress = 0.0
                
                return WorkflowStatusResponse(
                    workflow_id=workflow_id,
                    workflow_type=state.context.workflow_type.value,
                    status=state.status,
                    current_node=state.current_node,
                    progress=min(progress, 100.0),
                    start_time=state.start_time,
                    end_time=state.end_time,
                    duration=state.total_duration,
                    total_vulnerabilities=len(state.vulnerabilities),
                    node_results=state.node_results,
                    errors=state.errors,
                    metadata=state.context.metadata
                )
            
            # 如果内存中没有，从数据库获取
            if not self.storage._initialized:
                await self.storage.initialize()
            
            workflow_data = await self.storage.get_workflow(workflow_id)
            
            if not workflow_data:
                raise ValueError(f"工作流不存在: {workflow_id}")
            
            # 解析JSON字段
            import json
            errors = workflow_data.get("errors", "[]")
            if isinstance(errors, str):
                errors = json.loads(errors)
            
            metadata_str = workflow_data.get("meta_data", "{}")
            if isinstance(metadata_str, str):
                metadata = json.loads(metadata_str)
            else:
                metadata = metadata_str
            
            return WorkflowStatusResponse(
                workflow_id=workflow_id,
                workflow_type=workflow_data["workflow_type"],
                status=TaskStatus(workflow_data["status"]),
                current_node=workflow_data.get("current_node"),
                progress=100.0 if workflow_data["status"] in ["SUCCESS", "FAILED", "CANCELLED"] else 50.0,
                start_time=workflow_data.get("started_at"),
                end_time=workflow_data.get("completed_at"),
                duration=workflow_data.get("duration"),
                total_vulnerabilities=workflow_data.get("total_vulnerabilities", 0),
                node_results=[],
                errors=errors,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"获取工作流状态失败: {e}")
            raise
    
    async def pause(self, workflow_id: str) -> bool:
        """
        暂停工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功暂停
        """
        try:
            success = self.engine.pause_workflow(workflow_id)
            
            if success:
                # 更新数据库
                workflow = self.engine.get_workflow(workflow_id)
                if workflow:
                    await self.storage.save_workflow(workflow["state"])
            
            return success
            
        except Exception as e:
            logger.error(f"暂停工作流失败: {e}")
            return False
    
    async def resume(
        self,
        workflow_id: str,
        checkpoint_id: Optional[str] = None
    ) -> WorkflowExecutionResponse:
        """
        恢复工作流
        
        Args:
            workflow_id: 工作流ID
            checkpoint_id: checkpoint ID
            
        Returns:
            工作流执行响应
        """
        try:
            # 恢复执行
            final_state = self.engine.resume_workflow(workflow_id, checkpoint_id)
            
            # 保存到数据库
            await self.storage.save_workflow(final_state)
            
            return WorkflowExecutionResponse(
                workflow_id=workflow_id,
                status=final_state.status,
                message=f"工作流恢复执行{'成功' if final_state.status == TaskStatus.SUCCESS else '失败'}",
                summary=final_state.get_summary()
            )
            
        except Exception as e:
            error_msg = f"恢复工作流失败: {str(e)}"
            logger.error(error_msg)
            
            return WorkflowExecutionResponse(
                workflow_id=workflow_id,
                status=TaskStatus.FAILED,
                message=error_msg,
                summary={"error": error_msg}
            )
    
    async def cancel(self, workflow_id: str) -> bool:
        """
        取消工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功取消
        """
        try:
            success = self.engine.cancel_workflow(workflow_id)
            
            if success:
                # 更新数据库
                workflow = self.engine.get_workflow(workflow_id)
                if workflow:
                    await self.storage.save_workflow(workflow["state"])
            
            return success
            
        except Exception as e:
            logger.error(f"取消工作流失败: {e}")
            return False
    
    async def delete(self, workflow_id: str) -> bool:
        """
        删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功删除
        """
        try:
            # 先从内存中删除
            if workflow_id in self.engine.workflows:
                del self.engine.workflows[workflow_id]
            
            if workflow_id in self.engine.checkpoints:
                del self.engine.checkpoints[workflow_id]
            
            # 从数据库删除
            if not self.storage._initialized:
                await self.storage.initialize()
            
            success = await self.storage.delete_workflow(workflow_id)
            
            if success:
                logger.success(f"工作流已删除: {workflow_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除工作流失败: {e}")
            return False
    
    async def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        列出工作流的所有 checkpoint
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            checkpoint 列表
        """
        try:
            # 先从引擎获取
            checkpoints = self.engine.list_checkpoints(workflow_id)
            
            if checkpoints:
                return checkpoints
            
            # 从数据库获取
            if not self.storage._initialized:
                await self.storage.initialize()
            
            db_checkpoints = await self.storage.get_checkpoints(workflow_id)
            
            return [
                {
                    "checkpoint_id": cp["checkpoint_id"],
                    "node_name": cp["node_name"],
                    "created_at": cp["created_at"].isoformat()
                }
                for cp in db_checkpoints
            ]
            
        except Exception as e:
            logger.error(f"列出 checkpoint 失败: {e}")
            return []
    
    async def list_workflows(
        self,
        status: Optional[TaskStatus] = None,
        workflow_type: Optional[WorkflowType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出工作流
        
        Args:
            status: 状态过滤
            workflow_type: 类型过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            工作流列表
        """
        try:
            if not self.storage._initialized:
                await self.storage.initialize()
            
            workflows = await self.storage.query_workflows(
                status=status,
                workflow_type=workflow_type.value if workflow_type else None,
                limit=limit,
                offset=offset
            )
            
            return workflows
            
        except Exception as e:
            logger.error(f"列出工作流失败: {e}")
            return []
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        列出所有工作流模板
        
        Returns:
            模板列表
        """
        return list_templates()
    
    async def close(self):
        """关闭资源"""
        if self.storage:
            await self.storage.close()
        
        logger.info("WorkflowExecutor 已关闭")


# 全局执行器实例

_global_executor: Optional[WorkflowExecutor] = None


def get_executor() -> WorkflowExecutor:
    """获取全局执行器实例"""
    global _global_executor
    if _global_executor is None:
        _global_executor = WorkflowExecutor()
    return _global_executor


async def execute_workflow(
    workflow_type: WorkflowType,
    target_path: str,
    tool_ids: Optional[List[str]] = None,
    **kwargs
) -> WorkflowExecutionResponse:
    """
    便捷函数：执行工作流
    
    Args:
        workflow_type: 工作流类型
        target_path: 扫描目标路径
        tool_ids: 工具ID列表
        **kwargs: 其他参数
        
    Returns:
        工作流执行响应
    """
    executor = get_executor()
    
    request = WorkflowExecutionRequest(
        workflow_type=workflow_type,
        target=ScanTarget(path=target_path),
        tool_ids=tool_ids,
        metadata=kwargs
    )
    
    return await executor.execute(request)

