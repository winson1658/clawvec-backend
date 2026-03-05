"""
身份驗證端點測試

測試策略：
- 每個測試獨立（通過 conftest.py 的事務回滾）
- 正向路徑 + 邊界條件 + 錯誤路徑
- 不 mock 業務邏輯，使用真實 service（確保集成正確）
"""

import pytest


class TestRegister:
    def test_success(self, client):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": "Password123",
                "display_name": "新用戶",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["email"] == "new@example.com"
        assert "hashed_password" not in data["data"]

    def test_duplicate_email(self, client, test_user):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",  # 已存在
                "password": "Password123",
                "display_name": "重複",
            },
        )
        assert response.status_code == 409
        assert response.json()["error_code"] == "USER_ALREADY_EXISTS"

    def test_weak_password_no_digit(self, client):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "weak@example.com",
                "password": "NoDigitPass",
                "display_name": "弱密碼",
            },
        )
        assert response.status_code == 422

    def test_invalid_email(self, client):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "Password123",
                "display_name": "錯誤",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_success(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "Password123"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "WrongPass123"},
        )
        assert response.status_code == 401
        assert response.json()["error_code"] == "INVALID_CREDENTIALS"

    def test_nonexistent_user(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "Password123"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    def test_success(self, client, test_user):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "Password123"},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    def test_invalid_token(self, client):
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "totally.invalid.token"},
        )
        assert response.status_code == 401
