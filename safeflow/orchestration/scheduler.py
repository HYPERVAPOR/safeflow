"""
任务调度器

提供异步任务调度功能，支持并行执行、失败重试和超时控制。
"""
import asyncio
from typing import List, Callable, Any, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from safeflow.orchestration.config import WorkflowConfig, RetryConfig
from safeflow.orchestration.models import TaskStatus


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[float] = None
    max_retries: int = 3
    retry_delay: float = 5.0
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    task_name: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    retry_count: int = 0


class TaskScheduler:
    """
    任务调度器
    
    功能：
    1. 并行执行多个任务
    2. 支持失败重试
    3. 支持超时控制
    4. 支持优先级调度
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        初始化调度器
        
        Args:
            config: 工作流配置
        """
        self.config = config or WorkflowConfig()
        self.semaphore = asyncio.Semaphore(
            self.config.concurrency.max_parallel_tools
        )
        logger.info(
            f"TaskScheduler 初始化完成，"
            f"最大并发: {self.config.concurrency.max_parallel_tools}"
        )
    
    async def schedule_parallel(
        self,
        tasks: List[Task],
        fail_fast: bool = False
    ) -> List[TaskResult]:
        """
        并行调度任务
        
        Args:
            tasks: 任务列表
            fail_fast: 是否在第一个任务失败时立即停止
            
        Returns:
            任务结果列表
        """
        logger.info(f"开始并行调度 {len(tasks)} 个任务")
        
        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)
        
        # 并行执行
        if fail_fast:
            results = await self._execute_parallel_fail_fast(sorted_tasks)
        else:
            results = await self._execute_parallel_all(sorted_tasks)
        
        # 统计
        success_count = sum(1 for r in results if r.status == TaskStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == TaskStatus.FAILED)
        
        logger.info(
            f"并行调度完成，成功: {success_count}，失败: {failed_count}"
        )
        
        return results
    
    async def schedule_sequential(
        self,
        tasks: List[Task],
        stop_on_failure: bool = False
    ) -> List[TaskResult]:
        """
        顺序调度任务
        
        Args:
            tasks: 任务列表
            stop_on_failure: 是否在失败时停止
            
        Returns:
            任务结果列表
        """
        logger.info(f"开始顺序调度 {len(tasks)} 个任务")
        
        results = []
        
        for task in tasks:
            result = await self._execute_single_task(task)
            results.append(result)
            
            if stop_on_failure and result.status == TaskStatus.FAILED:
                logger.warning(f"任务 {task.task_name} 失败，停止后续任务")
                # 标记剩余任务为跳过
                remaining_tasks = tasks[len(results):]
                for remaining_task in remaining_tasks:
                    results.append(TaskResult(
                        task_id=remaining_task.task_id,
                        task_name=remaining_task.task_name,
                        status=TaskStatus.SKIPPED,
                        error="前序任务失败"
                    ))
                break
        
        success_count = sum(1 for r in results if r.status == TaskStatus.SUCCESS)
        logger.info(f"顺序调度完成，成功: {success_count}/{len(tasks)}")
        
        return results
    
    async def _execute_parallel_all(
        self,
        tasks: List[Task]
    ) -> List[TaskResult]:
        """并行执行所有任务（等待全部完成）"""
        coroutines = [self._execute_single_task(task) for task in tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(TaskResult(
                    task_id=tasks[i].task_id,
                    task_name=tasks[i].task_name,
                    status=TaskStatus.FAILED,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_parallel_fail_fast(
        self,
        tasks: List[Task]
    ) -> List[TaskResult]:
        """并行执行任务（快速失败）"""
        # 创建任务协程
        coroutines = [self._execute_single_task(task) for task in tasks]
        
        results = []
        try:
            # 等待第一个完成或失败
            for coro in asyncio.as_completed(coroutines):
                result = await coro
                results.append(result)
                
                if result.status == TaskStatus.FAILED:
                    logger.warning(f"任务 {result.task_name} 失败，取消其他任务")
                    # 取消其他任务
                    for c in coroutines:
                        if not c.done():
                            c.cancel()
                    break
        except asyncio.CancelledError:
            logger.warning("任务被取消")
        
        return results
    
    async def _execute_single_task(self, task: Task) -> TaskResult:
        """
        执行单个任务（带重试）
        
        Args:
            task: 任务定义
            
        Returns:
            任务结果
        """
        retry_count = 0
        last_error = None
        
        start_time = datetime.now()
        
        while retry_count <= task.max_retries:
            try:
                # 获取信号量（限制并发）
                async with self.semaphore:
                    logger.debug(f"执行任务: {task.task_name} (尝试 {retry_count + 1}/{task.max_retries + 1})")
                    
                    # 执行任务
                    if task.timeout:
                        result = await asyncio.wait_for(
                            self._run_task_func(task),
                            timeout=task.timeout
                        )
                    else:
                        result = await self._run_task_func(task)
                    
                    # 成功
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    return TaskResult(
                        task_id=task.task_id,
                        task_name=task.task_name,
                        status=TaskStatus.SUCCESS,
                        result=result,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        retry_count=retry_count
                    )
                    
            except asyncio.TimeoutError:
                last_error = f"任务超时（{task.timeout}秒）"
                logger.warning(f"任务 {task.task_name} {last_error}")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"任务 {task.task_name} 失败: {last_error}")
            
            # 重试逻辑
            retry_count += 1
            if retry_count <= task.max_retries:
                # 计算重试延迟（指数退避）
                delay = task.retry_delay
                if self.config.retry.exponential_backoff:
                    delay = min(
                        task.retry_delay * (self.config.retry.backoff_multiplier ** (retry_count - 1)),
                        self.config.retry.max_retry_delay
                    )
                
                logger.info(f"任务 {task.task_name} 将在 {delay} 秒后重试")
                await asyncio.sleep(delay)
        
        # 所有重试都失败
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return TaskResult(
            task_id=task.task_id,
            task_name=task.task_name,
            status=TaskStatus.FAILED,
            error=last_error,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            retry_count=retry_count - 1
        )
    
    async def _run_task_func(self, task: Task) -> Any:
        """运行任务函数"""
        # 判断是否为协程函数
        if asyncio.iscoroutinefunction(task.func):
            return await task.func(*task.args, **task.kwargs)
        else:
            # 同步函数在线程池中运行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: task.func(*task.args, **task.kwargs)
            )
    
    def handle_failure(
        self,
        task: Task,
        error: str
    ) -> Tuple[bool, Optional[int]]:
        """
        处理任务失败
        
        Args:
            task: 失败的任务
            error: 错误信息
            
        Returns:
            (是否重试, 重试延迟秒数)
        """
        if task.max_retries > 0:
            retry_delay = int(task.retry_delay)
            logger.info(f"任务 {task.task_name} 将重试，延迟 {retry_delay} 秒")
            return True, retry_delay
        else:
            logger.error(f"任务 {task.task_name} 失败且不重试: {error}")
            return False, None
    
    async def cancel_all(self):
        """取消所有正在执行的任务"""
        logger.warning("取消所有任务")
        # 获取当前事件循环中的所有任务
        tasks = [t for t in asyncio.all_tasks() if not t.done()]
        for task in tasks:
            task.cancel()
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"已取消 {len(tasks)} 个任务")


# 便捷函数

async def run_parallel(
    funcs: List[Callable],
    args_list: List[tuple] = None,
    kwargs_list: List[dict] = None,
    timeout: Optional[float] = None,
    max_concurrent: int = 4
) -> List[Any]:
    """
    并行运行多个函数（简化版）
    
    Args:
        funcs: 函数列表
        args_list: 参数列表
        kwargs_list: 关键字参数列表
        timeout: 超时时间
        max_concurrent: 最大并发数
        
    Returns:
        结果列表
    """
    if args_list is None:
        args_list = [()] * len(funcs)
    if kwargs_list is None:
        kwargs_list = [{}] * len(funcs)
    
    # 创建任务
    tasks = []
    for i, func in enumerate(funcs):
        task = Task(
            task_id=f"task_{i}",
            task_name=func.__name__,
            func=func,
            args=args_list[i],
            kwargs=kwargs_list[i],
            timeout=timeout
        )
        tasks.append(task)
    
    # 创建调度器并执行
    config = WorkflowConfig()
    config.concurrency.max_parallel_tools = max_concurrent
    scheduler = TaskScheduler(config)
    
    results = await scheduler.schedule_parallel(tasks)
    
    # 提取结果
    return [r.result if r.status == TaskStatus.SUCCESS else None for r in results]

