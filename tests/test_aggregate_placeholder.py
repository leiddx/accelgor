import uuid

import pytest
from fastapi.testclient import TestClient


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:6]}"


def issue_user_token(client: TestClient) -> str:
    username = unique_username("agg")
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

    return login_response.json()["access_token"]


def test_aggregate_placeholder_accepts_integer_in_range(client: TestClient) -> None:
    access_token = issue_user_token(client)

    response = client.get(
        "/api/v1/aggregate",
        params={"n": 100},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "aggregate placeholder",
        "n": 100,
    }


@pytest.mark.parametrize("value", [0, 101])
def test_aggregate_placeholder_rejects_integer_out_of_range(client: TestClient, value: int) -> None:
    access_token = issue_user_token(client)

    response = client.get(
        "/api/v1/aggregate",
        params={"n": value},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 422