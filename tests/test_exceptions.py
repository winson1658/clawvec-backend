"""
例外處理單元測試

驗證全局 exception handler 輸出格式一致。
"""

import pytest
from exceptions import (
    BadRequestError,
    AuthenticationError,
    UserAlreadyExistsError,
    PhilosophyNotFoundError,
    ClawvecException,
)


class TestExceptionHierarchy:
    def test_base_exception_fields(self):
        exc = ClawvecException(message="測試", detail={"key": "val"}, error_code="TEST")
        assert exc.message == "測試"
        assert exc.detail == {"key": "val"}
        assert exc.error_code == "TEST"

    def test_to_dict_includes_path(self):
        exc = BadRequestError(message="格式錯誤")
        d = exc.to_dict(path="/api/test")
        assert d["path"] == "/api/test"
        assert d["error_code"] == "BAD_REQUEST"
        assert d["message"] == "格式錯誤"

    def test_to_dict_omits_none_detail(self):
        exc = BadRequestError()
        d = exc.to_dict()
        assert "detail" not in d

    def test_inheritance(self):
        exc = UserAlreadyExistsError()
        assert isinstance(exc, ClawvecException)
        assert exc.status_code == 409
        assert exc.error_code == "USER_ALREADY_EXISTS"

    def test_philosophy_not_found_inherits_not_found(self):
        from exceptions import NotFoundError
        exc = PhilosophyNotFoundError()
        assert isinstance(exc, NotFoundError)
        assert exc.status_code == 404


class TestExceptionHandlerResponse:
    """通過 TestClient 驗證 HTTP 響應格式"""

    def test_404_returns_correct_format(self, client):
        response = client.get("/api/users/99999")
        assert response.status_code == 404
        body = response.json()
        assert "error_code" in body
        assert "message" in body

    def test_validation_error_format(self, client):
        response = client.post("/api/auth/register", json={"email": "bad"})
        assert response.status_code == 422
        body = response.json()
        assert body["error_code"] == "VALIDATION_ERROR"
        assert "detail" in body
        assert isinstance(body["detail"], list)
