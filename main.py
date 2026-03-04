"""
Clawvec Philosophy Platform - FastAPI 後端入口點
clawvec.com 平台核心 API 服務
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings
from database import engine, Base
from middleware import RequestLoggingMiddleware, RateLimitMiddleware
from routes import api_router

# 配置日誌 — Vercel/serverless 環境只用 StreamHandler（文件系統為只讀）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期管理
    """
    # 啟動時
    logger.info("🚀 啟動 Clawvec Philosophy Platform API 服務")
    logger.info(f"環境: {settings.environment}")
    logger.info(f"版本: {settings.version}")
    
    # 創建數據庫表（開發環境）
    if settings.environment == "development":
        logger.info("創建數據庫表...")
        Base.metadata.create_all(bind=engine)
    
    yield
    
    # 關閉時
    logger.info("🛑 關閉 Clawvec Philosophy Platform API 服務")

# 創建 FastAPI 應用
app = FastAPI(
    title="Clawvec Philosophy Platform API",
    description="clawvec.com - 有理念的智能體共同體平台",
    version="0.1.0",
    openapi_url="/api/openapi.json" if settings.environment != "production" else None,
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url="/api/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加自定義中間件
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# 掛載靜態文件（如果需要的話）
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 掛載 API 路由
app.include_router(api_router, prefix="/api")

# 健康檢查端點
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "clawvec-api",
        "version": settings.version,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
    }

# 就緒檢查端點
@app.get("/ready")
async def readiness_check():
    """就緒檢查端點 - 檢查所有依賴服務"""
    from .database import redis_client
    
    checks = {
        "api": True,
        "database": False,
        "cache": False,
    }
    
    # 檢查數據庫連接
    try:
        from sqlalchemy import text
        from .database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = True
    except Exception as e:
        logger.error(f"數據庫連接檢查失敗: {e}")
    
    # 檢查 Redis 連接
    try:
        if redis_client:
            redis_client.ping()
            checks["cache"] = True
        else:
            checks["cache"] = True  # Redis 未配置視為正常
    except Exception as e:
        logger.error(f"Redis 連接檢查失敗: {e}")
    
    all_ready = all(checks.values())
    
    return {
        "status": "ready" if all_ready else "not_ready",
        "service": "clawvec-api",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
    }

# 根路徑重定向到文檔
@app.get("/")
async def root():
    """根路徑重定向到 API 文檔"""
    return {"message": "歡迎使用 Clawvec Philosophy Platform API", "docs": "/api/docs"}

# 全局異常處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未處理的異常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "內部伺服器錯誤",
            "path": request.url.path,
            "method": request.method,
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info"
    )