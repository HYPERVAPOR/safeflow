"""创建编排引擎数据库表

Revision ID: 001_orchestration
Revises: 
Create Date: 2025-01-22 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_orchestration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：创建表"""
    
    # 创建工作流运行记录表
    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workflow_id', sa.String(length=64), nullable=False),
        sa.Column('workflow_type', sa.Enum(
            'CODE_COMMIT', 'DEPENDENCY_UPDATE', 'EMERGENCY_VULN', 
            'RELEASE_REGRESSION', 'CUSTOM',
            name='workflowtypedb'
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 
            'RETRY', 'PAUSED', 'CANCELLED', 'SKIPPED',
            name='taskstatusdb'
        ), nullable=False),
        sa.Column('current_node', sa.String(length=128), nullable=True),
        sa.Column('target_type', sa.String(length=64), nullable=False),
        sa.Column('target_path', sa.Text(), nullable=False),
        sa.Column('target_language', sa.String(length=64), nullable=True),
        sa.Column('target_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tool_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tool_options', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_vulnerabilities', sa.Integer(), nullable=True),
        sa.Column('total_errors', sa.Integer(), nullable=True),
        sa.Column('node_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
                sa.Column('created_by', sa.String(length=128), nullable=True),
                sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('requires_human_review', sa.Boolean(), nullable=True),
        sa.Column('human_review_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('state_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id'),
        comment='工作流运行记录表'
    )
    
    # 创建索引
    op.create_index('idx_workflow_type_status', 'workflow_runs', ['workflow_type', 'status'])
    op.create_index('idx_created_at', 'workflow_runs', ['created_at'])
    op.create_index('idx_status_created', 'workflow_runs', ['status', 'created_at'])
    op.create_index(op.f('ix_workflow_runs_workflow_id'), 'workflow_runs', ['workflow_id'])
    op.create_index(op.f('ix_workflow_runs_workflow_type'), 'workflow_runs', ['workflow_type'])
    op.create_index(op.f('ix_workflow_runs_status'), 'workflow_runs', ['status'])
    
    # 创建 Checkpoint 表
    op.create_table(
        'workflow_checkpoints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('checkpoint_id', sa.String(length=64), nullable=False),
        sa.Column('workflow_run_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(length=64), nullable=False),
        sa.Column('node_name', sa.String(length=128), nullable=False),
        sa.Column('node_type', sa.String(length=64), nullable=True),
                sa.Column('state_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
                sa.Column('compressed', sa.Boolean(), nullable=True),
                sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                sa.Column('state_size', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_run_id'], ['workflow_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('checkpoint_id'),
        comment='工作流 Checkpoint 表'
    )
    
    # 创建索引
    op.create_index('idx_workflow_checkpoint', 'workflow_checkpoints', ['workflow_id', 'created_at'])
    op.create_index('idx_checkpoint_created', 'workflow_checkpoints', ['created_at'])
    op.create_index(op.f('ix_workflow_checkpoints_checkpoint_id'), 'workflow_checkpoints', ['checkpoint_id'])
    op.create_index(op.f('ix_workflow_checkpoints_workflow_run_id'), 'workflow_checkpoints', ['workflow_run_id'])
    op.create_index(op.f('ix_workflow_checkpoints_workflow_id'), 'workflow_checkpoints', ['workflow_id'])
    
    # 创建任务执行记录表
    op.create_table(
        'task_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.String(length=64), nullable=False),
        sa.Column('workflow_run_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(length=64), nullable=False),
        sa.Column('task_type', sa.String(length=64), nullable=False),
        sa.Column('task_name', sa.String(length=128), nullable=False),
        sa.Column('tool_id', sa.String(length=128), nullable=True),
        sa.Column('tool_name', sa.String(length=128), nullable=True),
        sa.Column('node_name', sa.String(length=128), nullable=True),
        sa.Column('node_type', sa.String(length=64), nullable=True),
        sa.Column('status', sa.Enum(
            'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 
            'RETRY', 'PAUSED', 'CANCELLED', 'SKIPPED',
            name='taskstatusdb'
        ), nullable=False),
        sa.Column('vulnerability_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
                sa.Column('max_retries', sa.Integer(), nullable=True),
                sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                sa.ForeignKeyConstraint(['workflow_run_id'], ['workflow_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id'),
        comment='任务执行记录表'
    )
    
    # 创建索引
    op.create_index('idx_workflow_task', 'task_executions', ['workflow_id', 'task_type', 'started_at'])
    op.create_index('idx_task_status', 'task_executions', ['status', 'started_at'])
    op.create_index('idx_tool_execution', 'task_executions', ['tool_id', 'status'])
    op.create_index(op.f('ix_task_executions_task_id'), 'task_executions', ['task_id'])
    op.create_index(op.f('ix_task_executions_workflow_run_id'), 'task_executions', ['workflow_run_id'])
    op.create_index(op.f('ix_task_executions_workflow_id'), 'task_executions', ['workflow_id'])
    op.create_index(op.f('ix_task_executions_status'), 'task_executions', ['status'])
    
    # 创建工作流模板表
    op.create_table(
        'workflow_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('template_id', sa.String(length=64), nullable=False),
        sa.Column('template_name', sa.String(length=256), nullable=False),
        sa.Column('workflow_type', sa.Enum(
            'CODE_COMMIT', 'DEPENDENCY_UPDATE', 'EMERGENCY_VULN', 
            'RELEASE_REGRESSION', 'CUSTOM',
            name='workflowtypedb'
        ), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('nodes', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('edges', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('default_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('required_tools', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('optional_tools', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('version', sa.String(length=32), nullable=True),
                sa.Column('is_active', sa.Boolean(), nullable=True),
                sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_id'),
        comment='工作流模板表'
    )
    
    # 创建索引
    op.create_index('idx_template_type_active', 'workflow_templates', ['workflow_type', 'is_active'])
    op.create_index(op.f('ix_workflow_templates_template_id'), 'workflow_templates', ['template_id'])
    op.create_index(op.f('ix_workflow_templates_workflow_type'), 'workflow_templates', ['workflow_type'])


def downgrade() -> None:
    """降级：删除表"""
    
    # 删除表（按依赖关系倒序）
    op.drop_table('workflow_templates')
    op.drop_table('task_executions')
    op.drop_table('workflow_checkpoints')
    op.drop_table('workflow_runs')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS taskstatusdb')
    op.execute('DROP TYPE IF EXISTS workflowtypedb')

