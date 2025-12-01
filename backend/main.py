from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API router and settings
from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="SafeFlow API",
    description="基于 LLM Agent 的智能测试平台接入系统 API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "SafeFlow API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "safeflow-api"}


# Initialize MCP service on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        from app.services.mcp_service import mcp_service

        await mcp_service.initialize()
        print("✅ MCP service initialized successfully")
    except Exception as e:
        print(f"⚠️  MCP service initialization failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
