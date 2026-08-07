import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import aggregate as aggregate_module


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


def test_aggregate_placeholder_accepts_integer_in_range(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_cpu_task(
        min_seconds: int = 1,
        max_seconds: int = 10,
        timeout_seconds: float | None = None,
    ) -> int:
        return min_seconds

    monkeypatch.setattr(aggregate_module, "simulate_cpu_intensive_task", fake_cpu_task)

    access_token = issue_user_token(client)

    response = client.get(
        "/api/v1/aggregate",
        params={"n": 10, "max_concurrency": 3},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "aggregate completed"
    assert data["n"] == 10
    assert data["max_concurrency"] == 3
    assert data["success_count"] == 10
    assert data["failed_count"] == 0
    assert isinstance(data["total_elapsed_seconds"], float)
    assert len(data["results"]) == 10
    assert all(item["status"] == "success" for item in data["results"])


def test_aggregate_collects_timeout_error_in_aggregate(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_timeout_cpu_task(
        min_seconds: int = 1,
        max_seconds: int = 10,
        timeout_seconds: float | None = None,
    ) -> int:
        raise asyncio.TimeoutError("cpu task timeout")

    monkeypatch.setattr(aggregate_module, "simulate_cpu_intensive_task", fake_timeout_cpu_task)

    access_token = issue_user_token(client)

    response = client.get(
        "/api/v1/aggregate",
        params={"n": 2, "max_concurrency": 2, "cpu_timeout_seconds": 0.2},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success_count"] == 0
    assert data["failed_count"] == 2
    assert len(data["results"]) == 2
    assert all(item["status"] == "failed" for item in data["results"])
    assert all(item["error_type"] == "TimeoutError" for item in data["results"])


@pytest.mark.asyncio
async def test_simulate_cpu_intensive_task_can_raise_random_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(aggregate_module.random, "random", lambda: 0.0)

    with pytest.raises(RuntimeError, match="simulated random cpu task error"):
        await aggregate_module.simulate_cpu_intensive_task(error_probability=1.0)


@pytest.mark.parametrize("value", [0, 101])
def test_aggregate_placeholder_rejects_integer_out_of_range(client: TestClient, value: int) -> None:
    access_token = issue_user_token(client)

    response = client.get(
        "/api/v1/aggregate",
        params={"n": value},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 422