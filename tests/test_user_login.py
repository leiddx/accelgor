import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.models import Token


async def get_token_by_value(value: str) -> Token | None:
    return await Token.filter(value=value).first()


async def get_token_by_refresh(value: str) -> Token | None:
    return await Token.filter(refresh=value).first()


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def parse_api_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def test_login(client: TestClient) -> None:
    username = unique_username("alice_login")

    register_response = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "password": "secret123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/login",
        json={
            "username": username, 
            "password": "secret123"
        },
    )

    assert login_response.status_code == 200
    
    register_body = register_response.json()
    login_body = login_response.json()
    
    assert login_body["access_token"]
    assert login_body["refresh_token"]
    assert login_body["expires_at"]

    stored_token = asyncio.run(get_token_by_value(login_body["access_token"]))
    assert stored_token is not None
    assert stored_token.value == login_body["access_token"]
    assert normalize_utc(stored_token.expire) == normalize_utc(parse_api_datetime(login_body["expires_at"]))
    assert stored_token.refresh == login_body["refresh_token"]
    assert stored_token.scope == "user"
    assert stored_token.user_id == register_body["id"]


@pytest.mark.parametrize("identifier", ["13800000000", "alice@example.com"])
def test_login_accepts_phone_or_email_identifier(client: TestClient, identifier: str) -> None:
    username = unique_username("alice_login")

    register_response = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "password": "secret123",
            "phone": "13800000000",
            "email": "alice@example.com",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/login",
        json={"username": identifier, "password": "secret123"},
    )

    assert login_response.status_code == 200
    
    register_body = register_response.json()
    login_body = login_response.json()
    
    assert login_body["access_token"]
    assert login_body["refresh_token"]
    assert login_body["expires_at"]

    stored_token = asyncio.run(get_token_by_value(login_body["access_token"]))
    assert stored_token is not None
    assert stored_token.value == login_body["access_token"]
    assert normalize_utc(stored_token.expire) == normalize_utc(parse_api_datetime(login_body["expires_at"]))
    assert stored_token.refresh == login_body["refresh_token"]
    assert stored_token.scope == "user"
    assert stored_token.user_id == register_body["id"]


def test_refresh_token(client: TestClient) -> None:
    username = unique_username("alref")

    register_response = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "password": "secret123",
        },
    )
    assert register_response.status_code == 201
    register_body = register_response.json()

    login_response = client.post(
        "/api/v1/login",
        json={
            "username": username,
            "password": "secret123",
        },
    )
    assert login_response.status_code == 200
    login_body = login_response.json()

    refresh_response = client.put(
        "/api/v1/login",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
        json={"refresh": login_body["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert refresh_body["access_token"]
    assert refresh_body["refresh_token"]
    assert refresh_body["expires_at"]
    assert refresh_body["access_token"] != login_body["access_token"]
    assert refresh_body["refresh_token"] != login_body["refresh_token"]

    old_token = asyncio.run(get_token_by_value(login_body["access_token"]))
    assert old_token is None

    refreshed_token = asyncio.run(get_token_by_refresh(refresh_body["refresh_token"]))
    assert refreshed_token is not None
    assert refreshed_token.value == refresh_body["access_token"]
    assert refreshed_token.user_id == register_body["id"]


def test_refresh_token_rejects_mismatch_refresh(client: TestClient) -> None:
    username = unique_username("arfail")

    register_response = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "password": "secret123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/login",
        json={
            "username": username,
            "password": "secret123",
        },
    )
    assert login_response.status_code == 200
    login_body = login_response.json()

    refresh_response = client.put(
        "/api/v1/login",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
        json={"refresh": "wrong-refresh"},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json() == {
        "success": False,
        "code": "REFRESH_TOKEN_INVALID",
        "message": "刷新令牌错误",
    }
