"""
工作流状态持久化

提供与 PostgreSQL 的异步交互，存储和查询工作流执行状态。
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger


class DateTimeEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 datetime 对象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logger.warning("asyncpg 未安装，持久化功能将不可用")

from safeflow.orchestration.models import WorkflowState, TaskStatus, CheckpointData
from safeflow.orchestration.config import StorageConfig


class WorkflowStorage:
    """
    工作流存储
    
    功能：
    1. 保存工作流运行记录
    2. 保存 checkpoint
    3. 查询工作流状态
    4. 查询历史记录
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        """
        初始化存储
        
        Args:
            config: 存储配置
        """
        self.config = config or StorageConfig()
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        
        if not ASYNCPG_AVAILABLE:
            logger.warning("asyncpg 不可用，持久化功能将被禁用")
    
    async def initialize(self):
        """初始化数据库连接池"""
        if not ASYNCPG_AVAILABLE or self._initialized:
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                self.config.database_url,
                min_size=5,
                max_size=self.config.pool_size,
                max_inactive_connection_lifetime=self.config.pool_recycle,
                command_timeout=self.config.pool_timeout
            )
            self._initialized = True
            logger.success("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("数据库连接池已关闭")
    
    async def save_workflow(self, state: WorkflowState) -> int:
        """
        保存工作流运行记录
        
        Args:
            state: 工作流状态
            
        Returns:
            数据库记录ID
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # 将状态序列化为JSON
            state_snapshot = state.model_dump()
            
            query = """
                INSERT INTO workflow_runs (
                    workflow_id, workflow_type, status, current_node,
                    target_type, target_path, target_language, target_metadata,
                    tool_ids, tool_options,
                    total_vulnerabilities, total_errors, node_count,
                    created_at, started_at, completed_at, duration,
                    created_by, config, meta_data, tags,
                    requires_human_review, human_review_data,
                    errors, state_snapshot
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18,
                    $19, $20, $21, $22, $23, $24, $25
                )
                ON CONFLICT (workflow_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    current_node = EXCLUDED.current_node,
                    total_vulnerabilities = EXCLUDED.total_vulnerabilities,
                    total_errors = EXCLUDED.total_errors,
                    node_count = EXCLUDED.node_count,
                    completed_at = EXCLUDED.completed_at,
                    duration = EXCLUDED.duration,
                    requires_human_review = EXCLUDED.requires_human_review,
                    human_review_data = EXCLUDED.human_review_data,
                    errors = EXCLUDED.errors,
                    state_snapshot = EXCLUDED.state_snapshot,
                    meta_data = EXCLUDED.meta_data
                RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                row_id = await conn.fetchval(
                    query,
                    state.context.workflow_id,
                    state.context.workflow_type.value,
                    state.status.value,
                    state.current_node,
                    state.target.type,
                    state.target.path,
                    state.target.language,
                    json.dumps(state.target.metadata, cls=DateTimeEncoder),
                    json.dumps(state.tool_ids, cls=DateTimeEncoder),
                    json.dumps(state.tool_options, cls=DateTimeEncoder),
                    len(state.vulnerabilities),
                    len(state.errors),
                    len(state.node_results),
                    state.context.created_at,
                    state.start_time,
                    state.end_time,
                    state.total_duration,
                    state.context.created_by,
                    json.dumps(state.context.config, cls=DateTimeEncoder),
                    json.dumps(state.context.metadata, cls=DateTimeEncoder),
                    json.dumps(state.context.tags, cls=DateTimeEncoder),
                    state.requires_human_review,
                    json.dumps(state.human_review_data, cls=DateTimeEncoder) if state.human_review_data else None,
                    json.dumps(state.errors, cls=DateTimeEncoder),
                    json.dumps(state_snapshot, cls=DateTimeEncoder)
                )
            
            logger.debug(f"保存工作流: {state.context.workflow_id} (ID: {row_id})")
            return row_id
            
        except Exception as e:
            logger.error(f"保存工作流失败: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流记录
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流记录字典
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            query = "SELECT * FROM workflow_runs WHERE workflow_id = $1"
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, workflow_id)
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"获取工作流失败: {e}")
            raise
    
    async def save_checkpoint(
        self,
        checkpoint_data: CheckpointData
    ) -> int:
        """
        保存 checkpoint
        
        Args:
            checkpoint_data: checkpoint 数据
            
        Returns:
            数据库记录ID
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # 先获取 workflow_run_id
            workflow_run = await self.get_workflow(checkpoint_data.workflow_id)
            if not workflow_run:
                raise ValueError(f"工作流不存在: {checkpoint_data.workflow_id}")
            
            workflow_run_id = workflow_run["id"]
            
            query = """
                INSERT INTO workflow_checkpoints (
                    checkpoint_id, workflow_run_id, workflow_id,
                    node_name, node_type, state_data, compressed,
                    created_at, meta_data, state_size
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                )
                RETURNING id
            """
            
            state_json = json.dumps(checkpoint_data.state, cls=DateTimeEncoder)
            state_size = len(state_json.encode('utf-8'))
            
            async with self.pool.acquire() as conn:
                row_id = await conn.fetchval(
                    query,
                    checkpoint_data.checkpoint_id,
                    workflow_run_id,
                    checkpoint_data.workflow_id,
                    checkpoint_data.node_name,
                    None,  # node_type
                    state_json,
                    False,  # compressed
                    checkpoint_data.created_at,
                    json.dumps(checkpoint_data.metadata, cls=DateTimeEncoder),
                    state_size
                )
            
            logger.debug(
                f"保存 checkpoint: {checkpoint_data.checkpoint_id} "
                f"at {checkpoint_data.node_name}"
            )
            return row_id
            
        except Exception as e:
            logger.error(f"保存 checkpoint 失败: {e}")
            raise
    
    async def get_checkpoints(
        self,
        workflow_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取工作流的 checkpoint 列表
        
        Args:
            workflow_id: 工作流ID
            limit: 限制数量
            
        Returns:
            checkpoint 列表
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            query = """
                SELECT * FROM workflow_checkpoints
                WHERE workflow_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, workflow_id, limit)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取 checkpoint 列表失败: {e}")
            raise
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流及其相关数据
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功删除
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                # 先获取 workflow_run_id
                workflow_data = await conn.fetchrow(
                    "SELECT id FROM workflow_runs WHERE workflow_id = $1",
                    workflow_id
                )
                
                if not workflow_data:
                    logger.warning(f"工作流不存在: {workflow_id}")
                    return False
                
                workflow_run_id = workflow_data["id"]
                
                # 删除相关的任务执行记录
                await conn.execute(
                    "DELETE FROM task_executions WHERE workflow_run_id = $1",
                    workflow_run_id
                )
                
                # 删除相关的检查点
                await conn.execute(
                    "DELETE FROM workflow_checkpoints WHERE workflow_run_id = $1",
                    workflow_run_id
                )
                
                # 删除工作流记录
                await conn.execute(
                    "DELETE FROM workflow_runs WHERE id = $1",
                    workflow_run_id
                )
            
            logger.success(f"工作流已删除: {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除工作流失败: {e}")
            raise
    
    async def query_workflows(
        self,
        status: Optional[TaskStatus] = None,
        workflow_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询工作流列表
        
        Args:
            status: 状态过滤
            workflow_type: 类型过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            工作流列表
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            conditions = []
            params = []
            param_count = 0
            
            if status:
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(status.value)
            
            if workflow_type:
                param_count += 1
                conditions.append(f"workflow_type = ${param_count}")
                params.append(workflow_type)
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            param_count += 1
            params.append(limit)
            limit_param = f"${param_count}"
            
            param_count += 1
            params.append(offset)
            offset_param = f"${param_count}"
            
            query = f"""
                SELECT * FROM workflow_runs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit_param} OFFSET {offset_param}
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"查询工作流列表失败: {e}")
            raise
    
    async def save_task_execution(
        self,
        workflow_id: str,
        task_data: Dict[str, Any]
    ) -> int:
        """
        保存任务执行记录
        
        Args:
            workflow_id: 工作流ID
            task_data: 任务数据
            
        Returns:
            数据库记录ID
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # 获取 workflow_run_id
            workflow_run = await self.get_workflow(workflow_id)
            if not workflow_run:
                raise ValueError(f"工作流不存在: {workflow_id}")
            
            workflow_run_id = workflow_run["id"]
            
            query = """
                INSERT INTO task_executions (
                    task_id, workflow_run_id, workflow_id,
                    task_type, task_name, tool_id, tool_name,
                    node_name, node_type, status,
                    vulnerability_count, error_message,
                    started_at, completed_at, duration,
                    retry_count, max_retries,
                    input_data, output_data, meta_data
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                )
                RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                row_id = await conn.fetchval(query, *[
                    task_data.get("task_id"),
                    workflow_run_id,
                    workflow_id,
                    task_data.get("task_type"),
                    task_data.get("task_name"),
                    task_data.get("tool_id"),
                    task_data.get("tool_name"),
                    task_data.get("node_name"),
                    task_data.get("node_type"),
                    task_data.get("status"),
                    task_data.get("vulnerability_count", 0),
                    task_data.get("error_message"),
                    task_data.get("started_at"),
                    task_data.get("completed_at"),
                    task_data.get("duration"),
                    task_data.get("retry_count", 0),
                    task_data.get("max_retries", 3),
                    json.dumps(task_data.get("input_data", {}), cls=DateTimeEncoder),
                    json.dumps(task_data.get("output_data", {}), cls=DateTimeEncoder),
                    json.dumps(task_data.get("metadata", {}), cls=DateTimeEncoder)
                ])
            
            logger.debug(f"保存任务执行记录: {task_data.get('task_id')}")
            return row_id
            
        except Exception as e:
            logger.error(f"保存任务执行记录失败: {e}")
            raise


# 便捷函数

_global_storage: Optional[WorkflowStorage] = None


async def get_storage() -> WorkflowStorage:
    """获取全局存储实例"""
    global _global_storage
    if _global_storage is None:
        _global_storage = WorkflowStorage()
        await _global_storage.initialize()
    return _global_storage

