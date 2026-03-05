"""
FastAPI 路由包

api_router 被 main.py 導入並掛載到 /api 前綴。
新增路由模組時，在此 include 即可，main.py 無需修改。
"""

from fastapi import APIRouter

from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.philosophy import router as philosophy_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["身份驗證"])
api_router.include_router(users_router, prefix="/users", tags=["用戶"])
api_router.include_router(philosophy_router, prefix="/philosophy", tags=["理念"])

__all__ = ["api_router"]
