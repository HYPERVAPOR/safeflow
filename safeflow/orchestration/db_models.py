"""
编排引擎数据库模型

使用 SQLAlchemy 定义工作流、checkpoint、任务执行等数据库表结构。
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, JSON, Text, Boolean, 
    ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import enum


Base = declarative_base()


class TaskStatusDB(str, enum.Enum):
    """任务状态（数据库枚举）"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class WorkflowTypeDB(str, enum.Enum):
    """工作流类型（数据库枚举）"""
    CODE_COMMIT = "code_commit"
    DEPENDENCY_UPDATE = "dependency_update"
    EMERGENCY_VULN = "emergency_vuln"
    RELEASE_REGRESSION = "release_regression"
    CUSTOM = "custom"


class WorkflowRun(Base):
    """
    工作流运行记录表
    
    存储每次工作流执行的完整信息。
    """
    __tablename__ = "workflow_runs"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 工作流标识
    workflow_id = Column(String(64), unique=True, nullable=False, index=True, 
                         comment="工作流唯一ID")
    workflow_type = Column(SQLEnum(WorkflowTypeDB), nullable=False, index=True,
                           comment="工作流类型")
    
    # 状态
    status = Column(SQLEnum(TaskStatusDB), nullable=False, default=TaskStatusDB.PENDING,
                   index=True, comment="执行状态")
    current_node = Column(String(128), nullable=True, comment="当前节点")
    
    # 目标信息
    target_type = Column(String(64), nullable=False, comment="目标类型")
    target_path = Column(Text, nullable=False, comment="目标路径")
    target_language = Column(String(64), nullable=True, comment="编程语言")
    target_metadata = Column(JSON, nullable=True, comment="目标元数据")
    
    # 工具配置
    tool_ids = Column(JSON, nullable=True, comment="工具ID列表")
    tool_options = Column(JSON, nullable=True, comment="工具选项")
    
    # 执行结果
    total_vulnerabilities = Column(Integer, default=0, comment="总漏洞数")
    total_errors = Column(Integer, default=0, comment="总错误数")
    node_count = Column(Integer, default=0, comment="节点数量")
    
    # 时间统计
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True,
                       comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    duration = Column(Float, nullable=True, comment="执行时长（秒）")
    
    # 用户信息
    created_by = Column(String(128), nullable=True, comment="创建者")
    
    # 配置和元数据
    config = Column(JSON, nullable=True, comment="配置")
    meta_data = Column(JSON, nullable=True, comment="元数据")
    tags = Column(JSON, nullable=True, comment="标签")
    
    # 人工审查
    requires_human_review = Column(Boolean, default=False, comment="是否需要人工审查")
    human_review_data = Column(JSON, nullable=True, comment="人工审查数据")
    
    # 错误信息
    errors = Column(JSON, nullable=True, comment="错误列表")
    
    # 完整状态快照（用于恢复）
    state_snapshot = Column(JSON, nullable=True, comment="状态快照")
    
    # 关系
    checkpoints = relationship("WorkflowCheckpoint", back_populates="workflow_run",
                              cascade="all, delete-orphan")
    task_executions = relationship("TaskExecution", back_populates="workflow_run",
                                  cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_type_status', 'workflow_type', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
        {'comment': '工作流运行记录表'}
    )
    
    def __repr__(self):
        return f"<WorkflowRun(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"


class WorkflowCheckpoint(Base):
    """
    工作流 Checkpoint 表
    
    存储工作流执行过程中的状态快照，用于断点恢复。
    """
    __tablename__ = "workflow_checkpoints"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Checkpoint 标识
    checkpoint_id = Column(String(64), unique=True, nullable=False, index=True,
                          comment="Checkpoint 唯一ID")
    
    # 关联工作流
    workflow_run_id = Column(Integer, ForeignKey("workflow_runs.id", ondelete="CASCADE"),
                            nullable=False, index=True, comment="工作流运行ID")
    workflow_id = Column(String(64), nullable=False, index=True, comment="工作流ID")
    
    # 节点信息
    node_name = Column(String(128), nullable=False, comment="节点名称")
    node_type = Column(String(64), nullable=True, comment="节点类型")
    
    # 状态快照
    state_data = Column(JSON, nullable=False, comment="状态数据（序列化的 WorkflowState）")
    compressed = Column(Boolean, default=False, comment="是否压缩")
    
    # 时间信息
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True,
                       comment="创建时间")
    
    # 元数据
    meta_data = Column(JSON, nullable=True, comment="元数据")
    
    # 统计信息
    state_size = Column(Integer, nullable=True, comment="状态大小（字节）")
    
    # 关系
    workflow_run = relationship("WorkflowRun", back_populates="checkpoints")
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_checkpoint', 'workflow_id', 'created_at'),
        Index('idx_checkpoint_created', 'created_at'),
        {'comment': '工作流 Checkpoint 表'}
    )
    
    def __repr__(self):
        return f"<WorkflowCheckpoint(id={self.id}, checkpoint_id={self.checkpoint_id}, node={self.node_name})>"


class TaskExecution(Base):
    """
    任务执行记录表
    
    存储工作流中每个节点/工具的执行详情。
    """
    __tablename__ = "task_executions"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 任务标识
    task_id = Column(String(64), unique=True, nullable=False, index=True,
                    comment="任务唯一ID")
    
    # 关联工作流
    workflow_run_id = Column(Integer, ForeignKey("workflow_runs.id", ondelete="CASCADE"),
                            nullable=False, index=True, comment="工作流运行ID")
    workflow_id = Column(String(64), nullable=False, index=True, comment="工作流ID")
    
    # 任务类型
    task_type = Column(String(64), nullable=False, comment="任务类型（node/tool）")
    task_name = Column(String(128), nullable=False, comment="任务名称")
    
    # 工具信息（如果是工具执行）
    tool_id = Column(String(128), nullable=True, comment="工具ID")
    tool_name = Column(String(128), nullable=True, comment="工具名称")
    
    # 节点信息（如果是节点执行）
    node_name = Column(String(128), nullable=True, comment="节点名称")
    node_type = Column(String(64), nullable=True, comment="节点类型")
    
    # 状态
    status = Column(SQLEnum(TaskStatusDB), nullable=False, default=TaskStatusDB.PENDING,
                   index=True, comment="执行状态")
    
    # 执行结果
    vulnerability_count = Column(Integer, default=0, comment="发现漏洞数")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 时间统计
    started_at = Column(DateTime, nullable=False, default=func.now(), comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    duration = Column(Float, nullable=True, comment="执行时长（秒）")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 输入输出
    input_data = Column(JSON, nullable=True, comment="输入数据")
    output_data = Column(JSON, nullable=True, comment="输出数据")
    
    # 元数据
    meta_data = Column(JSON, nullable=True, comment="元数据")
    
    # 关系
    workflow_run = relationship("WorkflowRun", back_populates="task_executions")
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_task', 'workflow_id', 'task_type', 'started_at'),
        Index('idx_task_status', 'status', 'started_at'),
        Index('idx_tool_execution', 'tool_id', 'status'),
        {'comment': '任务执行记录表'}
    )
    
    def __repr__(self):
        return f"<TaskExecution(id={self.id}, task_name={self.task_name}, status={self.status})>"


class WorkflowTemplate(Base):
    """
    工作流模板表
    
    存储预定义的工作流模板配置。
    """
    __tablename__ = "workflow_templates"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 模板标识
    template_id = Column(String(64), unique=True, nullable=False, index=True,
                        comment="模板唯一ID")
    template_name = Column(String(256), nullable=False, comment="模板名称")
    
    # 工作流类型
    workflow_type = Column(SQLEnum(WorkflowTypeDB), nullable=False, index=True,
                           comment="工作流类型")
    
    # 描述
    description = Column(Text, nullable=True, comment="描述")
    
    # 模板定义
    nodes = Column(JSON, nullable=False, comment="节点列表")
    edges = Column(JSON, nullable=False, comment="边列表")
    default_config = Column(JSON, nullable=True, comment="默认配置")
    
    # 工具要求
    required_tools = Column(JSON, nullable=True, comment="必需的工具")
    optional_tools = Column(JSON, nullable=True, comment="可选的工具")
    
    # 版本控制
    version = Column(String(32), default="1.0.0", comment="版本号")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 时间信息
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), 
                       onupdate=func.now(), comment="更新时间")
    
    # 元数据
    meta_data = Column(JSON, nullable=True, comment="元数据")
    
    # 索引
    __table_args__ = (
        Index('idx_template_type_active', 'workflow_type', 'is_active'),
        {'comment': '工作流模板表'}
    )
    
    def __repr__(self):
        return f"<WorkflowTemplate(id={self.id}, template_name={self.template_name})>"

