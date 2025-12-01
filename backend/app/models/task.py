from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ExecutionStep(BaseModel):
    """执行步骤"""

    step_id: str = Field(..., description="步骤ID")
    name: str = Field(..., description="步骤名称")
    tool_id: str = Field(..., description="使用的工具ID")
    parameters: Dict[str, Any] = Field(..., description="执行参数")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="步骤状态")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TestTask(BaseModel):
    """测试任务"""

    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    description: str = Field(..., description="任务描述")
    target: str = Field(..., description="测试目标")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="任务优先级"
    )
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    execution_plan: List[ExecutionStep] = Field(..., description="执行计划")
    created_by: str = Field(..., description="创建者")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskCreateRequest(BaseModel):
    """创建任务请求"""

    task_name: str = Field(..., description="任务名称")
    description: str = Field(..., description="任务描述")
    target: str = Field(..., description="测试目标")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="任务优先级"
    )
    natural_language_request: Optional[str] = Field(None, description="自然语言请求")
