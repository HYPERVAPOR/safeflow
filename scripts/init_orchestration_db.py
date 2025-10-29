"""
初始化编排引擎数据库

创建数据库表并插入示例模板数据。

使用方法：
    python scripts/init_orchestration_db.py
    
环境变量：
    DATABASE_URL: 数据库连接字符串（可选，默认使用 alembic.ini 中的配置）
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

from safeflow.orchestration.db_models import Base, WorkflowTemplate, WorkflowTypeDB


def get_database_url() -> str:
    """获取数据库连接字符串"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://safeflow:safeflow@localhost:5432/safeflow"
    )


def create_tables(engine):
    """创建所有表"""
    logger.info("开始创建数据库表...")
    Base.metadata.create_all(engine)
    logger.success("数据库表创建完成！")


def insert_default_templates(session):
    """插入默认工作流模板"""
    logger.info("开始插入默认工作流模板...")
    
    templates = [
        {
            "template_id": "code_commit_v1",
            "template_name": "代码提交快速回归",
            "workflow_type": WorkflowTypeDB.CODE_COMMIT,
            "description": "用于代码提交后的快速安全回归测试，聚焦变更代码",
            "nodes": ["initialize", "scan", "collect", "finalize"],
            "edges": [
                {"from": "initialize", "to": "scan"},
                {"from": "scan", "to": "collect"},
                {"from": "collect", "to": "finalize"}
            ],
            "default_config": {
                "timeout": 1800,
                "max_parallel_tools": 2
            },
            "required_tools": ["semgrep"],
            "optional_tools": [],
            "version": "1.0.0",
            "is_active": True
        },
        {
            "template_id": "dependency_update_v1",
            "template_name": "依赖更新扫描验证",
            "workflow_type": WorkflowTypeDB.DEPENDENCY_UPDATE,
            "description": "重点进行SCA扫描与漏洞匹配",
            "nodes": ["initialize", "scan", "validate", "finalize"],
            "edges": [
                {"from": "initialize", "to": "scan"},
                {"from": "scan", "to": "validate"},
                {"from": "validate", "to": "finalize"}
            ],
            "default_config": {
                "timeout": 3600,
                "max_parallel_tools": 2
            },
            "required_tools": ["syft"],
            "optional_tools": ["dependency-check"],
            "version": "1.0.0",
            "is_active": True
        },
        {
            "template_id": "emergency_vuln_v1",
            "template_name": "紧急漏洞披露扫描",
            "workflow_type": WorkflowTypeDB.EMERGENCY_VULN,
            "description": "快速全量扫描与验证，针对特定CVE/CWE",
            "nodes": ["initialize", "parallel_scan", "collect", "validate", "finalize"],
            "edges": [
                {"from": "initialize", "to": "parallel_scan"},
                {"from": "parallel_scan", "to": "collect"},
                {"from": "collect", "to": "validate"},
                {"from": "validate", "to": "finalize"}
            ],
            "default_config": {
                "timeout": 3600,
                "max_parallel_tools": 6
            },
            "required_tools": ["semgrep", "syft"],
            "optional_tools": [],
            "version": "1.0.0",
            "is_active": True
        },
        {
            "template_id": "release_regression_v1",
            "template_name": "版本发布全链路回归",
            "workflow_type": WorkflowTypeDB.RELEASE_REGRESSION,
            "description": "完整的多阶段测试，包含人工审查环节",
            "nodes": ["initialize", "parallel_scan", "collect", "validate", "human_review", "finalize"],
            "edges": [
                {"from": "initialize", "to": "parallel_scan"},
                {"from": "parallel_scan", "to": "collect"},
                {"from": "collect", "to": "validate"},
                {"from": "validate", "to": "human_review"},
                {"from": "human_review", "to": "finalize"}
            ],
            "default_config": {
                "timeout": 43200,
                "max_parallel_tools": 4,
                "enable_human_review": True
            },
            "required_tools": ["semgrep", "syft"],
            "optional_tools": [],
            "version": "1.0.0",
            "is_active": True
        }
    ]
    
    for template_data in templates:
        # 检查模板是否已存在
        existing = session.query(WorkflowTemplate).filter_by(
            template_id=template_data["template_id"]
        ).first()
        
        if existing:
            logger.info(f"模板 {template_data['template_name']} 已存在，跳过")
            continue
        
        template = WorkflowTemplate(**template_data)
        session.add(template)
        logger.info(f"已插入模板: {template_data['template_name']}")
    
    session.commit()
    logger.success("默认工作流模板插入完成！")


def test_connection(engine):
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.success("数据库连接测试成功！")
            return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=== SafeFlow 编排引擎数据库初始化 ===")
    
    # 获取数据库 URL
    database_url = get_database_url()
    logger.info(f"数据库连接: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    # 创建引擎
    try:
        engine = create_engine(database_url, echo=False)
    except Exception as e:
        logger.error(f"创建数据库引擎失败: {e}")
        return False
    
    # 测试连接
    if not test_connection(engine):
        logger.error("请确保 PostgreSQL 已启动且数据库已创建")
        logger.info("创建数据库命令: CREATE DATABASE safeflow;")
        return False
    
    # 创建表
    try:
        create_tables(engine)
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        return False
    
    # 插入默认数据
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        insert_default_templates(session)
    except Exception as e:
        logger.error(f"插入默认数据失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()
    
    logger.success("=== 数据库初始化完成！===")
    logger.info("提示：也可以使用 Alembic 进行数据库迁移")
    logger.info("命令: alembic upgrade head")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

