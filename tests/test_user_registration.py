import os
import asyncio
import uuid

from fastapi.testclient import TestClient

from app.models import User


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


async def get_user_by_username(username: str) -> User:
    return await User.get(username=username)


def test_register_user_hashes_password_and_persists_optional_fields(client: TestClient) -> None:
    username = unique_username("alice_register_user")

    response = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == username
    assert response.json()["phone"] == ""
    assert response.json()["email"] == ""
    assert "password" not in response.json()

    user = asyncio.run(get_user_by_username(username))

    assert user.password != "secret123"
    assert user.phone == ""
    assert user.email == ""
    assert user.salt
    assert user.scope == "user"


def test_register_user_rejects_duplicate_username(client: TestClient) -> None:
    username = unique_username("alice_register_user_duplicate")

    payload = {
        "username": username,
        "password": "secret123",
        "phone": "13800000000",
        "email": "bob@example.com",
    }

    first_response = client.post("/api/v1/users", json=payload)
    second_response = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "password": "another-secret",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "用户名已存在"}