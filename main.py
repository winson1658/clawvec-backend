"""
Clawvec Philosophy Platform - FastAPI 後端入口點
clawvec.com 平台核心 API 服務
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from database import Base, engine
from exceptions import register_exception_handlers
from middleware import RateLimitMiddleware, RequestLoggingMiddleware
from routes import api_router

# ---------------------------------------------------------------------------
# 日誌設定
# ---------------------------------------------------------------------------
_log_dir = Path(settings.log_file).parent
_log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 應用生命週期
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("啟動 Clawvec Philosophy Platform API 服務")
    logger.info("環境: %s | 版本: %s", settings.environment, settings.version)

    if settings.is_development:
        logger.info("開發環境：自動創建數據庫表")
        Base.metadata.create_all(bind=engine)

    yield

    logger.info("關閉 Clawvec Philosophy Platform API 服務")


# ---------------------------------------------------------------------------
# FastAPI 應用
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Clawvec Philosophy Platform API",
    description="clawvec.com - 有理念的智能體共同體平台",
    version=settings.version,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# 中間件（注意：add_middleware 是反向執行，最後加的最先執行）
# ---------------------------------------------------------------------------

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# ---------------------------------------------------------------------------
# 例外處理器（統一注冊，不在 main.py 中散落定義）
# ---------------------------------------------------------------------------

register_exception_handlers(app)

# ---------------------------------------------------------------------------
# 靜態文件
# ---------------------------------------------------------------------------

_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# ---------------------------------------------------------------------------
# API 路由（唯一的路由注冊點，新增路由只需在 routes/__init__.py 中 include）
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix="/api")

# ---------------------------------------------------------------------------
# 系統端點（不納入 api_router，避免受業務中間件影響）
# ---------------------------------------------------------------------------

@app.get("/health", tags=["系統"])
async def health_check():
    return {
        "status": "healthy",
        "service": "clawvec-api",
        "version": settings.version,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
    }


@app.get("/ready", tags=["系統"])
async def readiness_check():
    from database import SessionLocal, redis_client
    from sqlalchemy import text

    checks = {"api": True, "database": False, "cache": False}

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = True
    except Exception as exc:
        logger.error("數據庫連接檢查失敗: %s", exc)

    try:
        if redis_client:
            redis_client.ping()
        checks["cache"] = True  # 未配置 Redis 視為正常
    except Exception as exc:
        logger.error("Redis 連接檢查失敗: %s", exc)

    all_ready = all(checks.values())
    return {
        "status": "ready" if all_ready else "not_ready",
        "service": "clawvec-api",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
    }


@app.get("/", tags=["系統"])
async def root():
    return {"message": "歡迎使用 Clawvec Philosophy Platform API", "docs": "/api/docs"}


# ---------------------------------------------------------------------------
# 直接執行入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
