"""
工作流演示脚本

演示4种业务场景的工作流执行。

使用方法：
    python scripts/workflow_demo.py [scenario]
    
场景：
    - code_commit: 代码提交快速回归
    - dependency_update: 依赖更新扫描
    - emergency_vuln: 紧急漏洞扫描
    - release_regression: 版本发布回归
    - all: 执行所有场景
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from safeflow.orchestration.executor import WorkflowExecutor
from safeflow.orchestration.models import (
    WorkflowExecutionRequest,
    WorkflowType,
    ScanTarget
)


async def demo_code_commit():
    """演示代码提交场景"""
    logger.info("=" * 60)
    logger.info("场景1：代码提交快速回归")
    logger.info("=" * 60)
    
    executor = WorkflowExecutor()
    
    request = WorkflowExecutionRequest(
        workflow_type=WorkflowType.CODE_COMMIT,
        target=ScanTarget(
            path=str(project_root / "vulnerable_code_examples"),
            language="python"
        ),
        tool_ids=["semgrep"],
        created_by="demo_user"
    )
    
    response = await executor.execute(request)
    
    logger.success(f"✅ 工作流ID: {response.workflow_id}")
    logger.success(f"✅ 状态: {response.status.value}")
    logger.success(f"✅ 消息: {response.message}")
    
    if response.summary:
        logger.info(f"📊 总漏洞数: {response.summary.get('total_vulnerabilities', 0)}")
        logger.info(f"📊 执行时长: {response.summary.get('duration', 0):.2f}秒")
    
    return response


async def demo_dependency_update():
    """演示依赖更新场景"""
    logger.info("=" * 60)
    logger.info("场景2：依赖更新扫描验证")
    logger.info("=" * 60)
    
    executor = WorkflowExecutor()
    
    request = WorkflowExecutionRequest(
        workflow_type=WorkflowType.DEPENDENCY_UPDATE,
        target=ScanTarget(
            path=str(project_root),
            language="python"
        ),
        tool_ids=["syft"],
        created_by="demo_user"
    )
    
    response = await executor.execute(request)
    
    logger.success(f"✅ 工作流ID: {response.workflow_id}")
    logger.success(f"✅ 状态: {response.status.value}")
    logger.success(f"✅ 消息: {response.message}")
    
    return response


async def demo_emergency_vuln():
    """演示紧急漏洞场景"""
    logger.info("=" * 60)
    logger.info("场景3：紧急漏洞披露扫描")
    logger.info("=" * 60)
    
    executor = WorkflowExecutor()
    
    request = WorkflowExecutionRequest(
        workflow_type=WorkflowType.EMERGENCY_VULN,
        target=ScanTarget(
            path=str(project_root / "vulnerable_code_examples"),
            language="python"
        ),
        tool_ids=["semgrep", "syft"],
        created_by="demo_user"
    )
    
    response = await executor.execute(request)
    
    logger.success(f"✅ 工作流ID: {response.workflow_id}")
    logger.success(f"✅ 状态: {response.status.value}")
    logger.success(f"✅ 消息: {response.message}")
    
    return response


async def demo_release_regression():
    """演示版本发布场景"""
    logger.info("=" * 60)
    logger.info("场景4：版本发布全链路回归")
    logger.info("=" * 60)
    
    executor = WorkflowExecutor()
    
    request = WorkflowExecutionRequest(
        workflow_type=WorkflowType.RELEASE_REGRESSION,
        target=ScanTarget(
            path=str(project_root / "safeflow"),
            language="python"
        ),
        tool_ids=["semgrep", "syft"],
        created_by="demo_user"
    )
    
    response = await executor.execute(request)
    
    logger.success(f"✅ 工作流ID: {response.workflow_id}")
    logger.success(f"✅ 状态: {response.status.value}")
    logger.success(f"✅ 消息: {response.message}")
    
    # 注意：此场景可能会暂停等待人工审查
    if response.summary and response.summary.get('status') == 'paused':
        logger.warning("⏸️  工作流已暂停，等待人工审查")
    
    return response


async def main():
    """主函数"""
    scenario = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    logger.info("🚀 SafeFlow 工作流演示")
    logger.info(f"📝 执行场景: {scenario}")
    logger.info("")
    
    try:
        if scenario == "code_commit" or scenario == "all":
            await demo_code_commit()
            print("\n")
        
        if scenario == "dependency_update" or scenario == "all":
            await demo_dependency_update()
            print("\n")
        
        if scenario == "emergency_vuln" or scenario == "all":
            await demo_emergency_vuln()
            print("\n")
        
        if scenario == "release_regression" or scenario == "all":
            await demo_release_regression()
            print("\n")
        
        logger.success("🎉 演示完成！")
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理资源
    from safeflow.orchestration.executor import get_executor
    executor = get_executor()
    await executor.close()


if __name__ == "__main__":
    asyncio.run(main())

