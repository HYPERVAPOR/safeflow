from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Create FastAPI application."""

    app = FastAPI(
        title="SafeFlow API",
        description="基于 LLM Agent 的智能测试平台接入系统 API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    # from app.api.v1 import api_router
    # app.include_router(api_router, prefix="/api/v1")

    return app