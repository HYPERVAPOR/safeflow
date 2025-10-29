"""
SafeFlow API 主应用

FastAPI 应用入口，整合所有路由。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger
import os

from safeflow.api.orchestration import router as orchestration_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("SafeFlow API 启动中...")
    
    # 注册安全工具适配器
    try:
        from safeflow.services.tool_registry import get_global_registry
        from safeflow.adapters.semgrep_adapter import SemgrepAdapter
        from safeflow.adapters.syft_adapter import SyftAdapter
        
        registry = get_global_registry()
        
        # 注册 Semgrep
        try:
            semgrep_adapter = SemgrepAdapter()
            registry.register(semgrep_adapter)
            logger.success("✓ Semgrep 适配器已注册")
        except Exception as e:
            logger.warning(f"Semgrep 适配器注册失败: {e}")
        
        # 注册 Syft
        try:
            syft_adapter = SyftAdapter()
            registry.register(syft_adapter)
            logger.success("✓ Syft 适配器已注册")
        except Exception as e:
            logger.warning(f"Syft 适配器注册失败: {e}")
        
        logger.info(f"已注册 {len(registry.list_all())} 个工具适配器")
    except Exception as e:
        logger.error(f"工具适配器注册失败: {e}")
    
    # 初始化数据库连接
    try:
        from safeflow.orchestration.storage import get_storage
        await get_storage()
        logger.success("✓ 数据库连接池已初始化")
    except Exception as e:
        logger.warning(f"数据库初始化失败: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("SafeFlow API 关闭中...")
    
    # 清理资源
    from safeflow.orchestration.executor import get_executor
    executor = get_executor()
    await executor.close()


# 创建FastAPI应用
app = FastAPI(
    title="SafeFlow",
    description="软件代码安全测评智能编排平台",
    version="0.1.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(orchestration_router)

# 静态文件服务（Web UI）
web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
if os.path.exists(web_dir):
    app.mount("/web", StaticFiles(directory=web_dir, html=True), name="web")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "SafeFlow API",
        "version": "0.1.0",
        "description": "软件代码安全测评智能编排平台",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    logger.info("启动 SafeFlow API 服务器...")
    uvicorn.run(
        "safeflow.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

