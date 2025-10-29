"""
SafeFlow 编排调度子系统

提供基于 LangGraph 的工作流编排、任务调度和状态管理功能。

主要模块：
- config: 编排配置
- models: 数据模型和 Schema
- db_models: 数据库模型
- engine: 核心编排引擎
- nodes: 工作流节点
- scheduler: 任务调度器
- templates: 业务场景工作流模板
- executor: 工作流执行器
- storage: 状态持久化
"""

__version__ = "0.1.0"

__all__ = [
    "OrchestrationEngine",
    "WorkflowExecutor",
    "TaskScheduler",
    "WorkflowStorage",
    "WorkflowState",
    "TaskStatus",
]

# 延迟导入，避免循环依赖
def __getattr__(name):
    if name == "OrchestrationEngine":
        from safeflow.orchestration.engine import OrchestrationEngine
        return OrchestrationEngine
    elif name == "WorkflowExecutor":
        from safeflow.orchestration.executor import WorkflowExecutor
        return WorkflowExecutor
    elif name == "TaskScheduler":
        from safeflow.orchestration.scheduler import TaskScheduler
        return TaskScheduler
    elif name == "WorkflowStorage":
        from safeflow.orchestration.storage import WorkflowStorage
        return WorkflowStorage
    elif name == "WorkflowState":
        from safeflow.orchestration.models import WorkflowState
        return WorkflowState
    elif name == "TaskStatus":
        from safeflow.orchestration.models import TaskStatus
        return TaskStatus
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

