"""
编排引擎

基于 LangGraph 实现有状态的工作流编排引擎。
"""
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from uuid import uuid4
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph 未安装，编排引擎将使用简化模式")

from safeflow.orchestration.models import (
    WorkflowState, WorkflowContext, WorkflowType,
    TaskStatus, ScanTarget
)
from safeflow.orchestration.config import WorkflowConfig
from safeflow.orchestration import nodes


class OrchestrationEngine:
    """
    编排引擎
    
    功能：
    1. 创建和管理工作流图
    2. 执行工作流
    3. 支持 checkpoint 和恢复
    4. 支持暂停和恢复
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        初始化编排引擎
        
        Args:
            config: 工作流配置
        """
        self.config = config or WorkflowConfig()
        self.workflows: Dict[str, Any] = {}  # 存储工作流实例
        self.checkpoints: Dict[str, List[Dict]] = {}  # 存储 checkpoint
        
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph 不可用，将使用简化的工作流执行模式")
        
        logger.info("OrchestrationEngine 初始化完成")
    
    def create_workflow(
        self,
        workflow_type: WorkflowType,
        target: ScanTarget,
        tool_ids: Optional[List[str]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> str:
        """
        创建工作流实例
        
        Args:
            workflow_type: 工作流类型
            target: 扫描目标
            tool_ids: 工具ID列表
            custom_config: 自定义配置
            created_by: 创建者
            
        Returns:
            工作流ID
        """
        workflow_id = str(uuid4())
        
        # 创建上下文
        context = WorkflowContext(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            created_by=created_by,
            config=custom_config or {},
            metadata={}
        )
        
        # 创建初始状态
        initial_state = WorkflowState(
            context=context,
            target=target,
            tool_ids=tool_ids or [],
            status=TaskStatus.PENDING
        )
        
        # 存储工作流
        self.workflows[workflow_id] = {
            "state": initial_state,
            "graph": None,  # 将在执行时构建
            "created_at": datetime.now()
        }
        
        logger.info(f"创建工作流: {workflow_id} ({workflow_type.value})")
        
        return workflow_id
    
    def execute_workflow(
        self,
        workflow_id: str,
        workflow_graph: Optional[Callable] = None
    ) -> WorkflowState:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            workflow_graph: 自定义工作流图构建函数
            
        Returns:
            最终的工作流状态
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        state = workflow["state"]
        
        logger.info(f"开始执行工作流: {workflow_id}")
        
        if LANGGRAPH_AVAILABLE and workflow_graph:
            # 使用 LangGraph 执行
            final_state = self._execute_with_langgraph(state, workflow_graph)
        else:
            # 使用简化模式执行
            final_state = self._execute_simple_mode(state)
        
        # 更新存储
        workflow["state"] = final_state
        
        logger.success(
            f"工作流执行完成: {workflow_id}，"
            f"状态: {final_state.status.value}"
        )
        
        return final_state
    
    def _execute_with_langgraph(
        self,
        state: WorkflowState,
        graph_builder: Callable
    ) -> WorkflowState:
        """使用 LangGraph 执行工作流"""
        # 构建图
        graph = graph_builder()
        
        # 执行
        try:
            final_state = graph.invoke(state)
            return final_state
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            state.status = TaskStatus.FAILED
            state.add_error(str(e))
            return state
    
    def _execute_simple_mode(self, state: WorkflowState) -> WorkflowState:
        """
        简化模式执行（不使用 LangGraph）
        
        按照预定义的顺序执行节点。
        """
        workflow_type = state.context.workflow_type
        
        # 根据工作流类型选择执行顺序
        if workflow_type == WorkflowType.CODE_COMMIT:
            node_sequence = [
                nodes.initialize_node,
                nodes.single_scan_node,
                nodes.result_collection_node,
                nodes.finalize_node
            ]
        elif workflow_type == WorkflowType.DEPENDENCY_UPDATE:
            node_sequence = [
                nodes.initialize_node,
                nodes.single_scan_node,
                nodes.validation_node,
                nodes.finalize_node
            ]
        elif workflow_type == WorkflowType.EMERGENCY_VULN:
            node_sequence = [
                nodes.initialize_node,
                nodes.parallel_scan_node,
                nodes.result_collection_node,
                nodes.validation_node,
                nodes.finalize_node
            ]
        elif workflow_type == WorkflowType.RELEASE_REGRESSION:
            node_sequence = [
                nodes.initialize_node,
                nodes.parallel_scan_node,
                nodes.result_collection_node,
                nodes.validation_node,
                nodes.human_review_node,
                nodes.finalize_node
            ]
        else:
            # 默认流程
            node_sequence = [
                nodes.initialize_node,
                nodes.single_scan_node,
                nodes.result_collection_node,
                nodes.finalize_node
            ]
        
        # 顺序执行节点
        for node_func in node_sequence:
            try:
                state = node_func(state)
                
                # 保存 checkpoint
                if self.config.checkpoint.enabled and self.config.checkpoint.auto_save:
                    self._save_checkpoint(state)
                
                # 检查是否需要暂停
                if state.is_paused():
                    logger.warning(
                        f"工作流 {state.context.workflow_id} 已暂停，"
                        f"等待人工审查"
                    )
                    break
                
                # 检查是否失败
                if state.status == TaskStatus.FAILED:
                    logger.error(f"工作流 {state.context.workflow_id} 执行失败")
                    break
                    
            except Exception as e:
                logger.error(f"节点执行异常: {e}")
                state.status = TaskStatus.FAILED
                state.add_error(f"节点 {node_func.__name__} 执行异常: {str(e)}")
                break
        
        return state
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """
        暂停工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功暂停
        """
        if workflow_id not in self.workflows:
            logger.error(f"工作流不存在: {workflow_id}")
            return False
        
        workflow = self.workflows[workflow_id]
        state = workflow["state"]
        
        if state.is_completed():
            logger.warning(f"工作流 {workflow_id} 已完成，无法暂停")
            return False
        
        state.status = TaskStatus.PAUSED
        logger.info(f"工作流 {workflow_id} 已暂停")
        
        return True
    
    def resume_workflow(
        self,
        workflow_id: str,
        checkpoint_id: Optional[str] = None
    ) -> WorkflowState:
        """
        恢复工作流
        
        Args:
            workflow_id: 工作流ID
            checkpoint_id: checkpoint ID（可选）
            
        Returns:
            最终的工作流状态
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        state = workflow["state"]
        
        # 从 checkpoint 恢复
        if checkpoint_id and workflow_id in self.checkpoints:
            checkpoints = self.checkpoints[workflow_id]
            checkpoint = next(
                (cp for cp in checkpoints if cp["checkpoint_id"] == checkpoint_id),
                None
            )
            if checkpoint:
                state = checkpoint["state"]
                logger.info(f"从 checkpoint {checkpoint_id} 恢复工作流 {workflow_id}")
        
        # 更新状态
        state.status = TaskStatus.RUNNING
        
        # 继续执行
        return self.execute_workflow(workflow_id)
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        取消工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功取消
        """
        if workflow_id not in self.workflows:
            logger.error(f"工作流不存在: {workflow_id}")
            return False
        
        workflow = self.workflows[workflow_id]
        state = workflow["state"]
        
        if state.is_completed():
            logger.warning(f"工作流 {workflow_id} 已完成，无法取消")
            return False
        
        state.status = TaskStatus.CANCELLED
        logger.info(f"工作流 {workflow_id} 已取消")
        
        return True
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流状态
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            状态字典
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        state = workflow["state"]
        
        return state.get_summary()
    
    def _save_checkpoint(self, state: WorkflowState) -> str:
        """
        保存 checkpoint
        
        Args:
            state: 工作流状态
            
        Returns:
            checkpoint ID
        """
        workflow_id = state.context.workflow_id
        checkpoint_id = str(uuid4())
        
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "workflow_id": workflow_id,
            "state": state,
            "node_name": state.current_node,
            "created_at": datetime.now()
        }
        
        if workflow_id not in self.checkpoints:
            self.checkpoints[workflow_id] = []
        
        self.checkpoints[workflow_id].append(checkpoint)
        
        # 限制 checkpoint 数量
        max_checkpoints = self.config.checkpoint.max_checkpoints
        if len(self.checkpoints[workflow_id]) > max_checkpoints:
            self.checkpoints[workflow_id] = self.checkpoints[workflow_id][-max_checkpoints:]
        
        state.checkpoint_id = checkpoint_id
        state.last_checkpoint_time = datetime.now()
        
        logger.debug(f"保存 checkpoint: {checkpoint_id} at {state.current_node}")
        
        return checkpoint_id
    
    def _load_checkpoint(
        self,
        workflow_id: str,
        checkpoint_id: str
    ) -> Optional[WorkflowState]:
        """
        加载 checkpoint
        
        Args:
            workflow_id: 工作流ID
            checkpoint_id: checkpoint ID
            
        Returns:
            工作流状态
        """
        if workflow_id not in self.checkpoints:
            logger.warning(f"工作流 {workflow_id} 没有 checkpoint")
            return None
        
        checkpoints = self.checkpoints[workflow_id]
        checkpoint = next(
            (cp for cp in checkpoints if cp["checkpoint_id"] == checkpoint_id),
            None
        )
        
        if checkpoint:
            logger.info(f"加载 checkpoint: {checkpoint_id}")
            return checkpoint["state"]
        else:
            logger.warning(f"Checkpoint {checkpoint_id} 不存在")
            return None
    
    def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        列出工作流的所有 checkpoint
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            checkpoint 列表
        """
        if workflow_id not in self.checkpoints:
            return []
        
        checkpoints = self.checkpoints[workflow_id]
        
        return [
            {
                "checkpoint_id": cp["checkpoint_id"],
                "node_name": cp["node_name"],
                "created_at": cp["created_at"].isoformat()
            }
            for cp in checkpoints
        ]
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流信息"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(
        self,
        status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        列出所有工作流
        
        Args:
            status: 状态过滤
            
        Returns:
            工作流列表
        """
        workflows = []
        
        for workflow_id, workflow in self.workflows.items():
            state = workflow["state"]
            
            if status is None or state.status == status:
                workflows.append({
                    "workflow_id": workflow_id,
                    "workflow_type": state.context.workflow_type.value,
                    "status": state.status.value,
                    "created_at": workflow["created_at"].isoformat(),
                    "summary": state.get_summary()
                })
        
        return workflows


# 便捷函数

def create_simple_workflow_graph() -> Callable:
    """
    创建简单的工作流图（LangGraph 版本）
    
    Returns:
        图构建函数
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph 未安装")
    
    def build_graph():
        # 创建状态图
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("initialize", nodes.initialize_node)
        workflow.add_node("scan", nodes.single_scan_node)
        workflow.add_node("collect", nodes.result_collection_node)
        workflow.add_node("finalize", nodes.finalize_node)
        
        # 添加边
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "scan")
        workflow.add_edge("scan", "collect")
        workflow.add_edge("collect", "finalize")
        workflow.add_edge("finalize", END)
        
        # 编译
        app = workflow.compile()
        
        return app
    
    return build_graph

