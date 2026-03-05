"""
Pytest 共享 Fixtures

架構：
- 使用 SQLite in-memory 作為測試數據庫（快速、無需外部依賴）
- 每個測試函數使用獨立事務（自動回滾），測試間互不污染
- TestClient 通過依賴覆蓋注入測試用 DB session

使用方式：
    def test_something(client, db_session, auth_headers):
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# 使用 SQLite 測試數據庫（每次 in-memory，快速隔離）
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """session 範圍的引擎：所有測試共用，避免反覆建表"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # 創建所有表
    from database import Base
    import models  # noqa: F401 — 確保所有模型已注冊

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """
    每個測試函數獲得獨立事務，測試結束後自動回滾。
    這樣每個測試從乾淨狀態開始，且無需清除數據。
    """
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    TestClient with DB session 依賴覆蓋。
    每個測試函數使用獨立的 DB session。
    """
    from main import app
    from database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # 回滾由 db_session fixture 負責

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """建立一個測試用戶並返回"""
    from models.user import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        email="test@example.com",
        hashed_password=pwd_context.hash("Password123"),
        display_name="測試用戶",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """取得已登入用戶的 Authorization headers"""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Password123"},
    )
    assert response.status_code == 200, f"登入失敗: {response.json()}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    """建立管理員用戶"""
    from models.user import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        email="admin@example.com",
        hashed_password=pwd_context.hash("AdminPass123"),
        display_name="管理員",
        is_active=True,
        is_verified=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.flush()
    return user
