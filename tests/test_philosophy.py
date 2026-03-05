"""
理念聲明端點測試
"""

import pytest


@pytest.fixture
def philosophy_data():
    return {
        "title": "開放協作理念",
        "content": "我相信知識應該開放共享，每個智能體都應該透明地聲明其理念並遵守。",
        "tag_ids": [],
    }


class TestListPhilosophy:
    def test_public_list(self, client):
        response = client.get("/api/philosophy/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    def test_pagination_params(self, client):
        response = client.get("/api/philosophy/?page=1&page_size=5")
        assert response.status_code == 200
        assert response.json()["page_size"] == 5

    def test_invalid_page(self, client):
        response = client.get("/api/philosophy/?page=0")
        assert response.status_code == 422


class TestCreatePhilosophy:
    def test_requires_auth(self, client, philosophy_data):
        response = client.post("/api/philosophy/", json=philosophy_data)
        assert response.status_code == 401

    def test_success(self, client, auth_headers, philosophy_data):
        response = client.post("/api/philosophy/", json=philosophy_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == philosophy_data["title"]
        assert data["id"] is not None

    def test_short_content_rejected(self, client, auth_headers):
        response = client.post(
            "/api/philosophy/",
            json={"title": "標題", "content": "太短", "tag_ids": []},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestUpdatePhilosophy:
    def test_owner_can_update(self, client, auth_headers, philosophy_data):
        create = client.post("/api/philosophy/", json=philosophy_data, headers=auth_headers)
        pid = create.json()["data"]["id"]

        response = client.patch(
            f"/api/philosophy/{pid}",
            json={"title": "更新後標題"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "更新後標題"

    def test_non_owner_forbidden(self, client, auth_headers, philosophy_data, db_session):
        # 以第一個用戶創建
        create = client.post("/api/philosophy/", json=philosophy_data, headers=auth_headers)
        pid = create.json()["data"]["id"]

        # 以第二個用戶嘗試修改
        from passlib.context import CryptContext
        from models.user import User
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        other = User(
            email="other@example.com",
            hashed_password=pwd.hash("Password123"),
            display_name="其他用戶",
            is_active=True,
        )
        db_session.add(other)
        db_session.flush()

        login = client.post(
            "/api/auth/login",
            json={"email": "other@example.com", "password": "Password123"},
        )
        other_token = login.json()["data"]["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = client.patch(
            f"/api/philosophy/{pid}",
            json={"title": "非法修改"},
            headers=other_headers,
        )
        assert response.status_code == 403


class TestDeletePhilosophy:
    def test_soft_delete(self, client, auth_headers, philosophy_data):
        create = client.post("/api/philosophy/", json=philosophy_data, headers=auth_headers)
        pid = create.json()["data"]["id"]

        response = client.delete(f"/api/philosophy/{pid}", headers=auth_headers)
        assert response.status_code == 200

        # 刪除後取得應返回 404
        get_resp = client.get(f"/api/philosophy/{pid}")
        assert get_resp.status_code == 404
