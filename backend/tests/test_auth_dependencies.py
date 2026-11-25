"""Authentication dependency and password-preparation tests."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import dependencies
import auth_service


def fake_request() -> Request:
    return Request({
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/me",
        "raw_path": b"/api/me",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    })


def test_missing_bearer_token_is_rejected():
    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(fake_request(), None)
    assert exc.value.status_code == 401


def test_invalid_jwt_is_rejected(monkeypatch):
    class InvalidAuth:
        @staticmethod
        def get_claims(jwt: str):
            raise ValueError("invalid signature")

    monkeypatch.setattr(dependencies, "get_database", lambda: SimpleNamespace(auth=InvalidAuth()))
    credentials = SimpleNamespace(credentials="not-a-valid-jwt")
    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(fake_request(), credentials)
    assert exc.value.status_code == 401


def test_password_preparation_uses_server_pepper(monkeypatch):
    monkeypatch.setattr(auth_service, "PASSWORD_PEPPER", "unit-test-secret-pepper")
    first = auth_service._prepared_password("ExamplePass123")
    second = auth_service._prepared_password("ExamplePass123")
    assert first == second
    assert first != "ExamplePass123"
    assert "ExamplePass123" not in first
