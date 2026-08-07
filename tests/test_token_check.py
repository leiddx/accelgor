import asyncio
import uuid

from fastapi.testclient import TestClient

from app.models import Token, User
from app.utils.time import utc_before


def unique_username(prefix: str) -> str:
	return f"{prefix}_{uuid.uuid4().hex[:8]}"


def issue_user_token(client: TestClient) -> tuple[str, dict]:
	username = unique_username("token_user")
	register_response = client.post(
		"/api/v1/users",
		json={"username": username, "password": "secret123"},
	)
	assert register_response.status_code == 201

	login_response = client.post(
		"/api/v1/login",
		json={"username": username, "password": "secret123"},
	)
	assert login_response.status_code == 200

	body = login_response.json()
	return body["access_token"], register_response.json()


async def mark_token_expired(token_value: str) -> None:
	await Token.filter(value=token_value).update(expire=utc_before(minutes=3))


async def elevate_user_scope(user_id: int) -> None:
	await User.filter(id=user_id).update(scope="admin")


def test_token_missing_returns_standard_failure(client: TestClient) -> None:
	response = client.get("/api/v1/users/me")

	assert response.status_code == 401
	assert response.json() == {
		"success": False,
		"code": "TOKEN_MISSING",
		"message": "缺少访问令牌",
	}


def test_token_invalid_returns_standard_failure(client: TestClient) -> None:
	response = client.get(
		"/api/v1/users/me",
		headers={"Authorization": "Bearer not-exists-token"},
	)

	assert response.status_code == 401
	assert response.json() == {
		"success": False,
		"code": "TOKEN_INVALID",
		"message": "访问令牌无效",
	}


def test_token_expired_returns_standard_failure(client: TestClient) -> None:
	access_token, _ = issue_user_token(client)
	asyncio.run(mark_token_expired(access_token))

	response = client.get(
		"/api/v1/users/me",
		headers={"Authorization": f"Bearer {access_token}"},
	)

	assert response.status_code == 401
	assert response.json() == {
		"success": False,
		"code": "TOKEN_EXPIRED",
		"message": "访问令牌已过期",
	}


def test_scope_forbidden_returns_standard_failure(client: TestClient) -> None:
	access_token, _ = issue_user_token(client)

	response = client.get(
		"/api/v1/users/admin/ping",
		headers={"Authorization": f"Bearer {access_token}"},
	)

	assert response.status_code == 403
	assert response.json() == {
		"success": False,
		"code": "SCOPE_FORBIDDEN",
		"message": "权限范围不足",
	}


def test_scope_passes_and_returns_user(client: TestClient) -> None:
	access_token, register_body = issue_user_token(client)

	response = client.get(
		"/api/v1/users/me",
		headers={"Authorization": f"Bearer {access_token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["id"] == register_body["id"]
	assert body["scope"] == "user"


def test_admin_scope_passes(client: TestClient) -> None:
	username = unique_username("token_admin")
	register_response = client.post(
		"/api/v1/users",
		json={"username": username, "password": "secret123"},
	)
	assert register_response.status_code == 201
	user_id = register_response.json()["id"]

	asyncio.run(elevate_user_scope(user_id))

	login_response = client.post(
		"/api/v1/login",
		json={"username": username, "password": "secret123"},
	)
	assert login_response.status_code == 200

	access_token = login_response.json()["access_token"]
	response = client.get(
		"/api/v1/users/admin/ping",
		headers={"Authorization": f"Bearer {access_token}"},
	)

	assert response.status_code == 200
	assert response.json() == {"status": "ok"}
