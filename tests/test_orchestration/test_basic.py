"""
编排引擎基础测试

测试核心功能的基本运行。
"""
import pytest
from safeflow.orchestration.models import (
    WorkflowState, WorkflowContext, WorkflowType,
    TaskStatus, ScanTarget
)
from safeflow.orchestration.config import WorkflowConfig
from safeflow.orchestration.engine import OrchestrationEngine


def test_workflow_state_creation():
    """测试工作流状态创建"""
    context = WorkflowContext(
        workflow_type=WorkflowType.CODE_COMMIT,
        created_by="test_user"
    )
    
    target = ScanTarget(path="/test/path")
    
    state = WorkflowState(
        context=context,
        target=target,
        tool_ids=["semgrep"]
    )
    
    assert state.context.workflow_type == WorkflowType.CODE_COMMIT
    assert state.target.path == "/test/path"
    assert len(state.tool_ids) == 1
    assert state.status == TaskStatus.PENDING


def test_engine_initialization():
    """测试引擎初始化"""
    config = WorkflowConfig()
    engine = OrchestrationEngine(config)
    
    assert engine.config is not None
    assert isinstance(engine.workflows, dict)


def test_workflow_creation():
    """测试工作流创建"""
    engine = OrchestrationEngine()
    
    workflow_id = engine.create_workflow(
        workflow_type=WorkflowType.CODE_COMMIT,
        target=ScanTarget(path="/test/path"),
        tool_ids=["semgrep"]
    )
    
    assert workflow_id is not None
    assert workflow_id in engine.workflows
    
    workflow = engine.get_workflow(workflow_id)
    assert workflow is not None
    assert workflow["state"].context.workflow_type == WorkflowType.CODE_COMMIT


def test_config_scenarios():
    """测试场景配置"""
    from safeflow.orchestration.config import get_config_for_scenario
    
    config = get_config_for_scenario("code_commit")
    assert config.timeout.workflow_timeout == 1800  # 30分钟
    
    config = get_config_for_scenario("release_regression")
    assert config.timeout.workflow_timeout == 43200  # 12小时


@pytest.mark.asyncio
async def test_templates():
    """测试工作流模板"""
    from safeflow.orchestration.templates import list_templates, get_template
    
    templates = list_templates()
    assert len(templates) == 4
    
    template = get_template(WorkflowType.CODE_COMMIT)
    assert template is not None
    assert template.get_template_name() == "代码提交快速回归"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

