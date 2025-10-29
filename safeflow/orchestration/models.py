"""
编排引擎数据模型

定义工作流状态、任务状态、上下文等核心数据结构。
使用 Pydantic 进行数据验证和序列化。
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "PENDING"          # 待执行
    RUNNING = "RUNNING"          # 执行中
    SUCCESS = "SUCCESS"          # 成功
    FAILED = "FAILED"            # 失败
    RETRY = "RETRY"              # 重试中
    PAUSED = "PAUSED"            # 暂停（等待人工审查）
    CANCELLED = "CANCELLED"      # 已取消
    SKIPPED = "SKIPPED"          # 已跳过


class WorkflowType(str, Enum):
    """工作流类型枚举"""
    CODE_COMMIT = "CODE_COMMIT"                  # 代码提交回归
    DEPENDENCY_UPDATE = "DEPENDENCY_UPDATE"      # 依赖更新扫描
    EMERGENCY_VULN = "EMERGENCY_VULN"            # 紧急漏洞扫描
    RELEASE_REGRESSION = "RELEASE_REGRESSION"    # 版本发布回归
    CUSTOM = "CUSTOM"                            # 自定义


class NodeType(str, Enum):
    """节点类型枚举"""
    INITIALIZE = "initialize"            # 初始化节点
    SCAN = "scan"                        # 扫描节点
    PARALLEL_SCAN = "parallel_scan"      # 并行扫描节点
    COLLECT = "collect"                  # 收集节点
    VALIDATE = "validate"                # 验证节点
    HUMAN_REVIEW = "human_review"        # 人工审查节点
    RETRY = "retry"                      # 重试节点
    FINALIZE = "finalize"                # 完成节点


class ScanTarget(BaseModel):
    """扫描目标"""
    model_config = ConfigDict(frozen=False)
    
    type: str = Field(default="LOCAL_PATH", description="目标类型")
    path: str = Field(..., description="目标路径")
    language: Optional[str] = Field(None, description="编程语言")
    branch: Optional[str] = Field(None, description="Git 分支")
    commit: Optional[str] = Field(None, description="Git 提交")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ToolExecutionResult(BaseModel):
    """工具执行结果"""
    model_config = ConfigDict(frozen=False)
    
    tool_id: str = Field(..., description="工具ID")
    tool_name: str = Field(..., description="工具名称")
    status: TaskStatus = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    vulnerability_count: int = Field(default=0, description="发现漏洞数")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class NodeResult(BaseModel):
    """节点执行结果"""
    model_config = ConfigDict(frozen=False)
    
    node_name: str = Field(..., description="节点名称")
    node_type: NodeType = Field(..., description="节点类型")
    status: TaskStatus = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    tool_results: List[ToolExecutionResult] = Field(default_factory=list, description="工具执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(default=0, description="重试次数")
    output: Dict[str, Any] = Field(default_factory=dict, description="输出数据")
    
    def is_success(self) -> bool:
        """判断是否成功"""
        return self.status == TaskStatus.SUCCESS
    
    def is_failed(self) -> bool:
        """判断是否失败"""
        return self.status == TaskStatus.FAILED
    
    def is_running(self) -> bool:
        """判断是否运行中"""
        return self.status == TaskStatus.RUNNING


class WorkflowContext(BaseModel):
    """工作流上下文"""
    model_config = ConfigDict(frozen=False)
    
    workflow_id: str = Field(default_factory=lambda: str(uuid4()), description="工作流ID")
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    created_by: Optional[str] = Field(None, description="创建者")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    tags: List[str] = Field(default_factory=list, description="标签")


class WorkflowState(BaseModel):
    """
    工作流状态（LangGraph 状态）
    
    这是 LangGraph 图中流转的核心数据结构，包含工作流执行的所有状态信息。
    """
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)
    
    # 基础信息
    context: WorkflowContext = Field(..., description="工作流上下文")
    target: ScanTarget = Field(..., description="扫描目标")
    
    # 执行状态
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="当前状态")
    current_node: Optional[str] = Field(None, description="当前节点")
    
    # 工具配置
    tool_ids: List[str] = Field(default_factory=list, description="要使用的工具ID列表")
    tool_options: Dict[str, Any] = Field(default_factory=dict, description="工具选项")
    
    # 执行结果
    node_results: List[NodeResult] = Field(default_factory=list, description="节点执行结果")
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list, description="发现的漏洞")
    
    # 错误处理
    errors: List[str] = Field(default_factory=list, description="错误列表")
    retry_count: int = Field(default=0, description="重试次数")
    
    # Checkpoint 相关
    checkpoint_id: Optional[str] = Field(None, description="当前 checkpoint ID")
    last_checkpoint_time: Optional[datetime] = Field(None, description="最后 checkpoint 时间")
    
    # 人工审查
    requires_human_review: bool = Field(default=False, description="是否需要人工审查")
    human_review_data: Optional[Dict[str, Any]] = Field(None, description="人工审查数据")
    
    # 统计信息
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    total_duration: Optional[float] = Field(None, description="总执行时长（秒）")
    
    def add_node_result(self, result: NodeResult) -> None:
        """添加节点结果"""
        self.node_results.append(result)
        self.current_node = result.node_name
        
        # 更新状态
        if result.is_failed():
            self.errors.append(f"节点 {result.node_name} 失败: {result.error}")
    
    def add_error(self, error: str) -> None:
        """添加错误"""
        self.errors.append(error)
    
    def is_completed(self) -> bool:
        """判断是否已完成"""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def is_paused(self) -> bool:
        """判断是否暂停"""
        return self.status == TaskStatus.PAUSED
    
    def get_total_vulnerabilities(self) -> int:
        """获取总漏洞数"""
        return len(self.vulnerabilities)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要信息"""
        return {
            "workflow_id": self.context.workflow_id,
            "workflow_type": self.context.workflow_type.value,
            "status": self.status.value,
            "current_node": self.current_node,
            "total_nodes": len(self.node_results),
            "total_vulnerabilities": self.get_total_vulnerabilities(),
            "total_errors": len(self.errors),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.total_duration,
        }


class WorkflowTemplate(BaseModel):
    """工作流模板"""
    model_config = ConfigDict(frozen=False)
    
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    description: str = Field(..., description="描述")
    nodes: List[str] = Field(..., description="节点列表")
    edges: List[Dict[str, str]] = Field(..., description="边列表")
    default_config: Dict[str, Any] = Field(default_factory=dict, description="默认配置")
    required_tools: List[str] = Field(default_factory=list, description="必需的工具")
    optional_tools: List[str] = Field(default_factory=list, description="可选的工具")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class CheckpointData(BaseModel):
    """Checkpoint 数据"""
    model_config = ConfigDict(frozen=False)
    
    checkpoint_id: str = Field(default_factory=lambda: str(uuid4()), description="Checkpoint ID")
    workflow_id: str = Field(..., description="工作流ID")
    state: Dict[str, Any] = Field(..., description="状态快照")
    node_name: str = Field(..., description="节点名称")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求"""
    model_config = ConfigDict(frozen=False)
    
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    target: ScanTarget = Field(..., description="扫描目标")
    tool_ids: Optional[List[str]] = Field(None, description="工具ID列表")
    config: Optional[Dict[str, Any]] = Field(None, description="配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    created_by: Optional[str] = Field(None, description="创建者")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    model_config = ConfigDict(frozen=False)
    
    workflow_id: str = Field(..., description="工作流ID")
    status: TaskStatus = Field(..., description="状态")
    message: str = Field(..., description="消息")
    summary: Optional[Dict[str, Any]] = Field(None, description="摘要")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    model_config = ConfigDict(frozen=False)
    
    workflow_id: str = Field(..., description="工作流ID")
    workflow_type: str = Field(..., description="工作流类型")
    status: TaskStatus = Field(..., description="状态")
    current_node: Optional[str] = Field(None, description="当前节点")
    progress: float = Field(..., description="进度百分比（0-100）")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    total_vulnerabilities: int = Field(default=0, description="总漏洞数")
    node_results: List[NodeResult] = Field(default_factory=list, description="节点结果")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

