"""
自定義中間件
"""

import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse
import uuid

from config import settings
from database import redis_client

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    請求日誌中間件
    記錄每個請求的詳細信息
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 生成請求 ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 記錄請求開始
        start_time = time.time()
        
        # 獲取客戶端信息
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 記錄請求信息（排除敏感路徑）
        request_path = request.url.path
        if not request_path.startswith(("/health", "/static")):
            logger.info(
                f"請求開始 | ID: {request_id} | "
                f"方法: {request.method} | 路徑: {request_path} | "
                f"客戶端: {client_host} | UA: {user_agent}"
            )
        
        try:
            # 處理請求
            response = await call_next(request)
            
            # 計算處理時間
            process_time = time.time() - start_time
            
            # 記錄響應信息
            if not request_path.startswith(("/health", "/static")):
                logger.info(
                    f"請求完成 | ID: {request_id} | "
                    f"狀態: {response.status_code} | "
                    f"耗時: {process_time:.3f}s"
                )
            
            # 添加響應頭
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as exc:
            # 記錄異常
            process_time = time.time() - start_time
            logger.error(
                f"請求異常 | ID: {request_id} | "
                f"異常: {type(exc).__name__}: {str(exc)} | "
                f"耗時: {process_time:.3f}s",
                exc_info=True
            )
            
            # 返回錯誤響應
            return JSONResponse(
                status_code=500,
                content={
                    "error": "內部伺服器錯誤",
                    "request_id": request_id,
                    "detail": str(exc) if settings.debug else "請聯繫管理員",
                }
            )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中間件
    基於 IP 地址的限制
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.redis = redis_client
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 如果 Redis 不可用，跳過速率限制
        if not self.redis:
            return await call_next(request)
        
        # 獲取客戶端 IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 排除健康檢查和靜態文件
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)
        
        # 構建 Redis 鍵
        rate_key = f"rate_limit:{client_ip}:{int(time.time() // settings.rate_limit_period)}"
        
        try:
            # 使用 Redis 原子操作增加計數器
            current = self.redis.incr(rate_key)
            
            # 如果是第一次設置，設置過期時間
            if current == 1:
                self.redis.expire(rate_key, settings.rate_limit_period)
            
            # 檢查是否超過限制
            if current > settings.rate_limit_requests:
                logger.warning(f"速率限制觸發 | IP: {client_ip} | 路徑: {request.url.path}")
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "請求過於頻繁",
                        "message": f"請等待 {settings.rate_limit_period} 秒後再試",
                        "retry_after": settings.rate_limit_period,
                    },
                    headers={"Retry-After": str(settings.rate_limit_period)}
                )
            
            # 添加速率限制頭
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
            response.headers["X-RateLimit-Remaining"] = str(max(0, settings.rate_limit_requests - current))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() // settings.rate_limit_period + 1) * settings.rate_limit_period)
            
            return response
            
        except Exception as e:
            logger.error(f"速率限制中間件錯誤: {e}")
            # 如果 Redis 出錯，跳過限制
            return await call_next(request)

class PhilosophyConsistencyMiddleware(BaseHTTPMiddleware):
    """
    理念一致性中間件（未來擴展）
    檢查智能體請求與其聲明理念的一致性
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 目前僅為佔位符，未來將實現理念一致性檢查
        # 檢查請求是否來自已驗證的智能體
        # 驗證請求行為與智能體理念聲明的一致性
        
        # 對於需要理念驗證的路徑
        if request.url.path.startswith("/api/philosophy") or request.url.path.startswith("/api/agent"):
            # 未來實現：檢查授權頭、驗證理念一致性
            pass
        
        response = await call_next(request)
        return response

# 創建中間件實例
request_logging_middleware = RequestLoggingMiddleware
rate_limit_middleware = RateLimitMiddleware
philosophy_consistency_middleware = PhilosophyConsistencyMiddleware

__all__ = [
    "RequestLoggingMiddleware",
    "RateLimitMiddleware", 
    "PhilosophyConsistencyMiddleware",
    "request_logging_middleware",
    "rate_limit_middleware",
    "philosophy_consistency_middleware",
]