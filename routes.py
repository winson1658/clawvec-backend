"""
API 路由匯總
將所有子路由器組合為一個 api_router
"""

from fastapi import APIRouter

api_router = APIRouter()

# 未來在此處 include 子路由器，例如:
# from routers import auth, agents, philosophy
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
# api_router.include_router(philosophy.router, prefix="/philosophy", tags=["philosophy"])
