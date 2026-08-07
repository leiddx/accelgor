import asyncio
import uuid

from fastapi.testclient import TestClient

from app.models import User


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def issue_user_token(client: TestClient) -> tuple[str, int, str]:
    username = unique_username("hello_user")
    register_response = client.post(
        "/api/v1/users",
        json={"username": username, "password": "secret123"},
    )
    assert register_response.status_code == 201

    user_id = register_response.json()["id"]
    login_response = client.post(
        "/api/v1/login",
        json={"username": username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    return access_token, user_id, username


async def elevate_user_scope(user_id: int) -> None:
    await User.filter(id=user_id).update(scope="admin")


def test_hello_user_requires_user_scope(client: TestClient) -> None:
    access_token, _, _ = issue_user_token(client)

    response = client.get(
        "/api/v1/hello/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == "Hello World"


def test_hello_admin_forbidden_for_user_scope(client: TestClient) -> None:
    access_token, _, _ = issue_user_token(client)

    response = client.get(
        "/api/v1/hello/admin",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "code": "SCOPE_FORBIDDEN",
        "message": "权限范围不足",
    }


def test_hello_admin_passes_for_admin_scope(client: TestClient) -> None:
    _, user_id, username = issue_user_token(client)
    asyncio.run(elevate_user_scope(user_id))

    admin_login = client.post(
        "/api/v1/login",
        json={"username": username, "password": "secret123"},
    )
    assert admin_login.status_code == 200

    admin_token = admin_login.json()["access_token"]
    response = client.get(
        "/api/v1/hello/admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json() == "Hello World"
