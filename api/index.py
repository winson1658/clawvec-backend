"""
Clawvec Philosophy Platform - Vercel Serverless Entry Point

This file is the single entry point for all Vercel serverless requests.
All routes (including /api/auth/* and /api/philosophy/*) are handled here
via FastAPI + Mangum ASGI adapter.

Root cause of previous 404 on /api/auth/*:
  - No vercel.json existed to configure routing
  - No api/index.py existed as a Vercel serverless handler
  - FastAPI (ASGI) requires Mangum adapter to run on Vercel/Lambda
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from mangum import Mangum

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Settings (read from environment variables, matching config.py conventions)
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", os.getenv("JWT_ALGORITHM", "HS256"))
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",
              os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
)
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://clawvec.com,https://www.clawvec.com",
    ).split(",")
    if o.strip()
]

# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def _create_token(data: Dict[str, Any], expires_delta: timedelta, token_type: str) -> str:
    payload = {**data, "exp": datetime.utcnow() + expires_delta, "type": token_type}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: Dict[str, Any]) -> str:
    return _create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(data: Dict[str, Any]) -> str:
    return _create_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效或已過期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token 類型錯誤，需要 {expected_type}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    return decode_token(credentials.credentials, "access")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Clawvec Philosophy Platform API",
    description="clawvec.com - 有理念的智能體共同體平台",
    version="0.1.0",
    # Disable docs in production to avoid leaking schema
    openapi_url="/api/openapi.json" if ENVIRONMENT != "production" else None,
    docs_url="/api/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Auth routes  (/api/auth/*)
# ---------------------------------------------------------------------------

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """
    用戶注冊

    TODO: Replace the stub token payload with a real database write.
    The hashed password is computed here; persist it in your User table.
    """
    hashed_password = pwd_context.hash(body.password)
    logger.info("register attempt: email=%s username=%s", body.email, body.username)

    # --- stub: replace with actual DB insert ---
    user_id = f"stub_{body.username}"
    # -------------------------------------------

    token_data = {"sub": user_id, "email": body.email}
    return {
        "message": "注冊成功",
        "user": {
            "id": user_id,
            "email": body.email,
            "username": body.username,
            "display_name": body.display_name or body.username,
        },
        "tokens": {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    }


@app.post("/api/auth/login")
async def login(body: LoginRequest):
    """
    用戶登入

    TODO: Look up the user by email in the database, verify
    ``pwd_context.verify(body.password, user.hashed_password)``, and raise
    HTTP 401 on mismatch.  The stub below always succeeds.
    """
    logger.info("login attempt: email=%s", body.email)

    # --- stub: replace with actual DB lookup + password verify ---
    user_id = "stub_user"
    # -------------------------------------------------------------

    token_data = {"sub": user_id, "email": body.email}
    return {
        "message": "登入成功",
        "user": {"id": user_id, "email": body.email},
        "tokens": {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    }


@app.post("/api/auth/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    用戶登出

    TODO: Add the access token to a Redis blacklist so it cannot be reused
    before it naturally expires.
    """
    logger.info("logout: user=%s", current_user.get("sub"))
    return {"message": "登出成功"}


@app.post("/api/auth/refresh")
async def refresh(body: RefreshRequest):
    """刷新 Access Token"""
    payload = decode_token(body.refresh_token, "refresh")
    token_data = {"sub": payload["sub"], "email": payload.get("email")}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.get("/api/auth/me")
async def me(current_user: Dict = Depends(get_current_user)):
    """獲取當前登入用戶資訊"""
    return {
        "id": current_user.get("sub"),
        "email": current_user.get("email"),
    }


# ---------------------------------------------------------------------------
# Philosophy routes  (/api/philosophy/*)
# ---------------------------------------------------------------------------

@app.get("/api/philosophy")
async def list_philosophies():
    """獲取理念列表 (TODO: query database)"""
    return {"philosophies": [], "total": 0}


@app.get("/api/philosophy/{philosophy_id}")
async def get_philosophy(philosophy_id: str):
    """獲取單一理念詳情 (TODO: query database)"""
    return {"id": philosophy_id, "message": "理念詳情"}


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "clawvec-api",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
    }


@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "service": "clawvec-api",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
async def root():
    return {
        "message": "歡迎使用 Clawvec Philosophy Platform API",
        "docs": "/api/docs",
    }


# ---------------------------------------------------------------------------
# Vercel / AWS Lambda handler (Mangum wraps the ASGI app)
# lifespan="off" disables startup/shutdown events which are not supported in
# serverless environments.
# ---------------------------------------------------------------------------
handler = Mangum(app, lifespan="off")
