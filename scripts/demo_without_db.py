"""
无需数据库的演示脚本

演示编排引擎的核心功能，不依赖 PostgreSQL。
工作流状态仅保存在内存中。

使用方法：
    python scripts/demo_without_db.py
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from safeflow.orchestration.engine import OrchestrationEngine
from safeflow.orchestration.models import (
    WorkflowType,
    ScanTarget
)
from safeflow.services.tool_registry import get_global_registry
from safeflow.adapters.semgrep_adapter import SemgrepAdapter
from safeflow.adapters.syft_adapter import SyftAdapter


async def demo_code_commit():
    """演示代码提交场景（无需数据库）"""
    logger.info("=" * 60)
    logger.info("场景1：代码提交快速回归（内存模式）")
    logger.info("=" * 60)
    
    # 注册工具
    registry = get_global_registry()
    try:
        registry.register(SemgrepAdapter())
        logger.info("✅ Semgrep 工具已注册")
    except Exception as e:
        logger.warning(f"Semgrep 注册失败: {e}")
    
    # 创建引擎（不使用存储）
    engine = OrchestrationEngine()
    
    # 创建工作流
    workflow_id = engine.create_workflow(
        workflow_type=WorkflowType.CODE_COMMIT,
        target=ScanTarget(
            path=str(project_root / "vulnerable_code_examples"),
            language="python"
        ),
        tool_ids=["semgrep"],
        created_by="demo_user"
    )
    
    logger.info(f"📝 工作流已创建: {workflow_id}")
    
    # 执行工作流
    final_state = engine.execute_workflow(workflow_id)
    
    # 显示结果
    logger.success("=" * 60)
    logger.success("执行结果")
    logger.success("=" * 60)
    logger.success(f"✅ 工作流ID: {workflow_id}")
    logger.success(f"✅ 状态: {final_state.status.value}")
    logger.success(f"✅ 执行节点数: {len(final_state.node_results)}")
    logger.success(f"✅ 发现漏洞数: {len(final_state.vulnerabilities)}")
    
    if final_state.errors:
        logger.warning(f"⚠️  错误数: {len(final_state.errors)}")
        for error in final_state.errors[:3]:
            logger.warning(f"   - {error}")
    
    # 显示节点执行情况
    logger.info("\n节点执行情况:")
    for node_result in final_state.node_results:
        status_icon = "✅" if node_result.is_success() else "❌"
        logger.info(
            f"  {status_icon} {node_result.node_name}: "
            f"{node_result.status.value} "
            f"({node_result.duration:.2f}s)"
        )
    
    return final_state


async def demo_dependency_scan():
    """演示依赖扫描场景"""
    logger.info("\n" + "=" * 60)
    logger.info("场景2：依赖更新扫描（内存模式）")
    logger.info("=" * 60)
    
    # 注册 Syft
    registry = get_global_registry()
    try:
        registry.register(SyftAdapter())
        logger.info("✅ Syft 工具已注册")
    except Exception as e:
        logger.warning(f"Syft 注册失败: {e}")
    
    # 创建引擎
    engine = OrchestrationEngine()
    
    # 创建工作流
    workflow_id = engine.create_workflow(
        workflow_type=WorkflowType.DEPENDENCY_UPDATE,
        target=ScanTarget(
            path=str(project_root),
            language="python"
        ),
        tool_ids=["syft"],
        created_by="demo_user"
    )
    
    logger.info(f"📝 工作流已创建: {workflow_id}")
    
    # 执行工作流
    final_state = engine.execute_workflow(workflow_id)
    
    # 显示结果
    logger.success("=" * 60)
    logger.success("执行结果")
    logger.success("=" * 60)
    logger.success(f"✅ 工作流ID: {workflow_id}")
    logger.success(f"✅ 状态: {final_state.status.value}")
    logger.success(f"✅ 发现的软件包: {len(final_state.vulnerabilities)}")
    
    return final_state


async def main():
    """主函数"""
    logger.info("🚀 SafeFlow 编排引擎演示（无数据库模式）")
    logger.info("📝 工作流状态仅保存在内存中\n")
    
    try:
        # 演示1：代码提交扫描
        await demo_code_commit()
        
        # 演示2：依赖扫描
        await demo_dependency_scan()
        
        logger.success("\n🎉 演示完成！")
        logger.info("\n💡 提示：")
        logger.info("  - 此演示不需要数据库，工作流状态仅保存在内存中")
        logger.info("  - 要使用完整功能（持久化、Web API），请安装 PostgreSQL")
        logger.info("  - 安装命令: bash /tmp/setup_postgres.sh")
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

