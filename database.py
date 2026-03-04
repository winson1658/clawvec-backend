"""
數據庫配置與連接管理
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

from config import settings

logger = logging.getLogger(__name__)

# 創建數據庫引擎
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # 30分鐘
    echo=settings.debug,
    future=True,
)

# 創建會話工廠
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# 創建基類
Base = declarative_base()

# 添加引擎事件監聽
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.debug("數據庫連接建立")

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("數據庫連接取出")

@event.listens_for(engine, "checkin")
def checkin(dbapi_connection, connection_record):
    logger.debug("數據庫連接歸還")

@event.listens_for(engine, "close")
def close(dbapi_connection, connection_record):
    logger.debug("數據庫連接關閉")

def get_db() -> Generator[Session, None, None]:
    """
    依賴注入用數據庫會話
    
    使用方式:
    ```
    from .database import get_db
    from fastapi import Depends
    
    @app.get("/items")
    async def read_items(db: Session = Depends(get_db)):
        # 使用 db 會話
        pass
    ```
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"數據庫操作失敗: {e}")
        raise
    finally:
        db.close()

async def get_db_async() -> Generator[Session, None, None]:
    """
    異步版本的數據庫會話獲取
    """
    return get_db()

def init_db():
    """
    初始化數據庫，創建所有表
    """
    logger.info("初始化數據庫...")
    Base.metadata.create_all(bind=engine)
    logger.info("數據庫初始化完成")

def drop_db():
    """
    刪除所有表（僅用於測試）
    """
    logger.warning("刪除數據庫所有表...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("數據庫表已刪除")

# Redis 連接（可選）
try:
    import redis
    redis_client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    
    # 測試 Redis 連接
    redis_client.ping()
    logger.info("Redis 連接成功")
    
except ImportError:
    logger.warning("Redis 未安裝，緩存功能將不可用")
    redis_client = None
except Exception as e:
    logger.warning(f"Redis 連接失敗: {e}，緩存功能將不可用")
    redis_client = None

# 導入所有模型以確保 SQLAlchemy 註冊它們
try:
    import models  # noqa: F401
except ImportError:
    pass

# 導出
__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_db_async",
    "init_db",
    "drop_db",
    "redis_client",
]