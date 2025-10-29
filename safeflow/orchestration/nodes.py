"""
工作流节点

定义 LangGraph 工作流中的各个节点函数。
每个节点接收 WorkflowState 并返回更新后的状态。
"""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from safeflow.orchestration.models import (
    WorkflowState, TaskStatus, NodeResult, NodeType,
    ToolExecutionResult, ScanTarget
)
from safeflow.services.tool_service import ToolService, ScanRequest
from safeflow.services.tool_registry import get_global_registry


# ===== 辅助函数 =====

def _create_node_result(
    node_name: str,
    node_type: NodeType,
    status: TaskStatus,
    start_time: datetime,
    end_time: datetime = None,
    error: str = None,
    tool_results: List[ToolExecutionResult] = None,
    output: Dict[str, Any] = None
) -> NodeResult:
    """创建节点结果"""
    end_time = end_time or datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    return NodeResult(
        node_name=node_name,
        node_type=node_type,
        status=status,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        tool_results=tool_results or [],
        error=error,
        output=output or {}
    )


def _should_retry(state: WorkflowState, max_retries: int = 3) -> bool:
    """判断是否应该重试"""
    return state.retry_count < max_retries


# ===== 核心节点函数 =====

def initialize_node(state: WorkflowState) -> WorkflowState:
    """
    初始化节点
    
    功能：
    1. 验证输入参数
    2. 初始化工作流状态
    3. 准备执行环境
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "initialize"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 开始初始化节点")
    
    try:
        # 验证目标路径
        if not state.target.path:
            raise ValueError("扫描目标路径不能为空")
        
        # 验证工具列表
        if not state.tool_ids:
            logger.warning("未指定工具，将使用所有已注册的工具")
            registry = get_global_registry()
            state.tool_ids = registry.get_tool_ids()
        
        # 更新状态
        state.status = TaskStatus.RUNNING
        state.start_time = start_time
        state.current_node = node_name
        
        # 创建节点结果
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.INITIALIZE,
            status=TaskStatus.SUCCESS,
            start_time=start_time,
            output={
                "workflow_id": state.context.workflow_id,
                "target_path": state.target.path,
                "tool_count": len(state.tool_ids),
                "tools": state.tool_ids
            }
        )
        
        state.add_node_result(result)
        
        logger.success(f"[{state.context.workflow_id}] 初始化完成，将使用 {len(state.tool_ids)} 个工具")
        
    except Exception as e:
        error_msg = f"初始化失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.INITIALIZE,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.status = TaskStatus.FAILED
        state.add_error(error_msg)
    
    return state


def single_scan_node(state: WorkflowState) -> WorkflowState:
    """
    单工具扫描节点
    
    顺序执行每个工具的扫描。
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "single_scan"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 开始单工具扫描")
    
    try:
        # 创建工具服务
        registry = get_global_registry()
        tool_service = ToolService(registry)
        
        # 构建扫描请求
        scan_request = ScanRequest(
            scan_id=state.context.workflow_id,
            target_path=state.target.path,
            tool_ids=state.tool_ids,
            options=state.tool_options
        )
        
        # 顺序执行扫描
        tool_results = []
        all_vulnerabilities = []
        
        for tool_id in state.tool_ids:
            logger.info(f"[{state.context.workflow_id}] 执行工具: {tool_id}")
            
            tool_start = datetime.now()
            response = tool_service.scan_with_tool(tool_id, scan_request)
            tool_end = datetime.now()
            
            # 记录工具执行结果
            tool_result = ToolExecutionResult(
                tool_id=tool_id,
                tool_name=response.metadata.get("tool_name", tool_id),
                status=TaskStatus.SUCCESS if response.success else TaskStatus.FAILED,
                start_time=tool_start,
                end_time=tool_end,
                duration=(tool_end - tool_start).total_seconds(),
                vulnerability_count=len(response.vulnerabilities),
                error=response.error,
                metadata=response.metadata
            )
            tool_results.append(tool_result)
            
            # 收集漏洞
            if response.success:
                for vuln in response.vulnerabilities:
                    vuln_dict = vuln.model_dump()
                    vuln_dict["source_tool"] = tool_id
                    all_vulnerabilities.append(vuln_dict)
        
        # 更新状态
        state.vulnerabilities.extend(all_vulnerabilities)
        
        # 创建节点结果
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.SCAN,
            status=TaskStatus.SUCCESS,
            start_time=start_time,
            tool_results=tool_results,
            output={
                "total_tools": len(state.tool_ids),
                "successful_tools": sum(1 for r in tool_results if r.status == TaskStatus.SUCCESS),
                "total_vulnerabilities": len(all_vulnerabilities)
            }
        )
        
        state.add_node_result(result)
        
        logger.success(
            f"[{state.context.workflow_id}] 扫描完成，"
            f"发现 {len(all_vulnerabilities)} 个问题"
        )
        
    except Exception as e:
        error_msg = f"扫描失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.SCAN,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.add_error(error_msg)
    
    return state


def parallel_scan_node(state: WorkflowState) -> WorkflowState:
    """
    并行扫描节点
    
    并行执行多个工具的扫描（使用 TaskScheduler）。
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "parallel_scan"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 开始并行扫描")
    
    try:
        # 创建工具服务
        registry = get_global_registry()
        tool_service = ToolService(registry)
        
        # 构建扫描请求
        scan_request = ScanRequest(
            scan_id=state.context.workflow_id,
            target_path=state.target.path,
            tool_ids=state.tool_ids,
            options=state.tool_options
        )
        
        # 并行执行扫描（目前使用顺序执行，后续集成 TaskScheduler 实现真正的并行）
        responses = tool_service.scan_with_multiple_tools(scan_request)
        
        # 处理结果
        tool_results = []
        all_vulnerabilities = []
        
        for response in responses:
            tool_result = ToolExecutionResult(
                tool_id=response.tool_id,
                tool_name=response.metadata.get("tool_name", response.tool_id),
                status=TaskStatus.SUCCESS if response.success else TaskStatus.FAILED,
                start_time=response.completed_at,
                end_time=response.completed_at,
                duration=0,  # 需要从 response 获取
                vulnerability_count=len(response.vulnerabilities),
                error=response.error,
                metadata=response.metadata
            )
            tool_results.append(tool_result)
            
            # 收集漏洞
            if response.success:
                for vuln in response.vulnerabilities:
                    vuln_dict = vuln.model_dump()
                    vuln_dict["source_tool"] = response.tool_id
                    all_vulnerabilities.append(vuln_dict)
        
        # 更新状态
        state.vulnerabilities.extend(all_vulnerabilities)
        
        # 创建节点结果
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.PARALLEL_SCAN,
            status=TaskStatus.SUCCESS,
            start_time=start_time,
            tool_results=tool_results,
            output={
                "total_tools": len(responses),
                "successful_tools": sum(1 for r in responses if r.success),
                "total_vulnerabilities": len(all_vulnerabilities)
            }
        )
        
        state.add_node_result(result)
        
        logger.success(
            f"[{state.context.workflow_id}] 并行扫描完成，"
            f"发现 {len(all_vulnerabilities)} 个问题"
        )
        
    except Exception as e:
        error_msg = f"并行扫描失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.PARALLEL_SCAN,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.add_error(error_msg)
    
    return state


def result_collection_node(state: WorkflowState) -> WorkflowState:
    """
    结果收集节点
    
    收集和聚合所有工具的扫描结果。
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "collect"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 开始收集结果")
    
    try:
        # 统计漏洞
        total_vulns = len(state.vulnerabilities)
        
        # 按严重度分组
        severity_count = {}
        for vuln in state.vulnerabilities:
            severity = vuln.get("severity", {}).get("level", "UNKNOWN")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        # 按工具分组
        tool_count = {}
        for vuln in state.vulnerabilities:
            tool = vuln.get("source_tool", "UNKNOWN")
            tool_count[tool] = tool_count.get(tool, 0) + 1
        
        # 创建节点结果
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.COLLECT,
            status=TaskStatus.SUCCESS,
            start_time=start_time,
            output={
                "total_vulnerabilities": total_vulns,
                "severity_distribution": severity_count,
                "tool_distribution": tool_count
            }
        )
        
        state.add_node_result(result)
        
        logger.success(
            f"[{state.context.workflow_id}] 结果收集完成，"
            f"共 {total_vulns} 个问题"
        )
        
    except Exception as e:
        error_msg = f"结果收集失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.COLLECT,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.add_error(error_msg)
    
    return state


def validation_node(state: WorkflowState) -> WorkflowState:
    """
    验证节点
    
    对检测结果进行验证和过滤。
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "validate"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 开始验证结果")
    
    try:
        # 简单验证逻辑（后续可扩展）
        validated_vulns = []
        filtered_count = 0
        
        for vuln in state.vulnerabilities:
            # 过滤低置信度的漏洞
            confidence = vuln.get("severity", {}).get("confidence_score", 0)
            if confidence >= 0.3:  # 置信度阈值
                validated_vulns.append(vuln)
            else:
                filtered_count += 1
        
        # 更新漏洞列表
        original_count = len(state.vulnerabilities)
        state.vulnerabilities = validated_vulns
        
        # 创建节点结果
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.VALIDATE,
            status=TaskStatus.SUCCESS,
            start_time=start_time,
            output={
                "original_count": original_count,
                "validated_count": len(validated_vulns),
                "filtered_count": filtered_count
            }
        )
        
        state.add_node_result(result)
        
        logger.success(
            f"[{state.context.workflow_id}] 验证完成，"
            f"保留 {len(validated_vulns)}/{original_count} 个问题"
        )
        
    except Exception as e:
        error_msg = f"验证失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.VALIDATE,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.add_error(error_msg)
    
    return state


def human_review_node(state: WorkflowState) -> WorkflowState:
    """
    人工审查节点
    
    暂停工作流，等待人工审查和决策。
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "human_review"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 进入人工审查节点")
    
    try:
        # 标记需要人工审查
        state.requires_human_review = True
        state.status = TaskStatus.PAUSED
        
        # 准备审查数据
        state.human_review_data = {
            "total_vulnerabilities": len(state.vulnerabilities),
            "critical_count": sum(
                1 for v in state.vulnerabilities 
                if v.get("severity", {}).get("level") == "CRITICAL"
            ),
            "high_count": sum(
                1 for v in state.vulnerabilities 
                if v.get("severity", {}).get("level") == "HIGH"
            ),
            "review_required_at": datetime.now().isoformat(),
            "message": "请审查扫描结果并决定是否继续"
        }
        
        # 创建节点结果
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.HUMAN_REVIEW,
            status=TaskStatus.PAUSED,
            start_time=start_time,
            output=state.human_review_data
        )
        
        state.add_node_result(result)
        
        logger.warning(
            f"[{state.context.workflow_id}] 工作流已暂停，等待人工审查"
        )
        
    except Exception as e:
        error_msg = f"人工审查节点失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.HUMAN_REVIEW,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.add_error(error_msg)
    
    return state


def retry_node(state: WorkflowState) -> WorkflowState:
    """
    重试节点
    
    处理失败任务的重试逻辑。
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "retry"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 进入重试节点")
    
    try:
        if _should_retry(state):
            state.retry_count += 1
            state.status = TaskStatus.RETRY
            
            logger.info(
                f"[{state.context.workflow_id}] 第 {state.retry_count} 次重试"
            )
            
            # 创建节点结果
            result = _create_node_result(
                node_name=node_name,
                node_type=NodeType.RETRY,
                status=TaskStatus.SUCCESS,
                start_time=start_time,
                output={"retry_count": state.retry_count}
            )
            
            state.add_node_result(result)
        else:
            # 超过最大重试次数
            state.status = TaskStatus.FAILED
            error_msg = f"已达到最大重试次数 ({state.retry_count})"
            state.add_error(error_msg)
            
            result = _create_node_result(
                node_name=node_name,
                node_type=NodeType.RETRY,
                status=TaskStatus.FAILED,
                start_time=start_time,
                error=error_msg
            )
            
            state.add_node_result(result)
            
            logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
    except Exception as e:
        error_msg = f"重试节点失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.RETRY,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.add_error(error_msg)
    
    return state


def finalize_node(state: WorkflowState) -> WorkflowState:
    """
    完成节点
    
    清理资源，生成最终报告，更新状态。
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的工作流状态
    """
    node_name = "finalize"
    start_time = datetime.now()
    
    logger.info(f"[{state.context.workflow_id}] 开始完成节点")
    
    try:
        # 计算总执行时长
        state.end_time = start_time
        if state.start_time:
            state.total_duration = (state.end_time - state.start_time).total_seconds()
        
        # 确定最终状态
        if state.status != TaskStatus.FAILED and state.status != TaskStatus.CANCELLED:
            state.status = TaskStatus.SUCCESS
        
        # 生成最终摘要
        summary = {
            "workflow_id": state.context.workflow_id,
            "workflow_type": state.context.workflow_type.value,
            "final_status": state.status.value,
            "total_nodes": len(state.node_results),
            "total_vulnerabilities": len(state.vulnerabilities),
            "total_errors": len(state.errors),
            "total_duration": state.total_duration,
            "start_time": state.start_time.isoformat() if state.start_time else None,
            "end_time": state.end_time.isoformat() if state.end_time else None,
        }
        
        # 创建节点结果
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.FINALIZE,
            status=TaskStatus.SUCCESS,
            start_time=start_time,
            output=summary
        )
        
        state.add_node_result(result)
        
        logger.success(
            f"[{state.context.workflow_id}] 工作流完成，"
            f"状态: {state.status.value}，"
            f"耗时: {state.total_duration:.2f}秒"
        )
        
    except Exception as e:
        error_msg = f"完成节点失败: {str(e)}"
        logger.error(f"[{state.context.workflow_id}] {error_msg}")
        
        result = _create_node_result(
            node_name=node_name,
            node_type=NodeType.FINALIZE,
            status=TaskStatus.FAILED,
            start_time=start_time,
            error=error_msg
        )
        
        state.add_node_result(result)
        state.add_error(error_msg)
        state.status = TaskStatus.FAILED
    
    return state

