"""测试环境固定使用内存 sqlite，避免依赖真实 MySQL 实例，需在导入 app 前设置。"""

import os
import asyncio
import pytest
import pytest_asyncio

from tortoise import Tortoise
from fastapi.testclient import TestClient
from collections.abc import AsyncGenerator, Generator

from app.main import app
from app.models import Token, User

os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")
os.environ.setdefault("DEBUG", "true")


@pytest_asyncio.fixture()
async def initialized_tortoise() -> AsyncGenerator[None, None]:
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()
    try:
        yield
    finally:
        await Tortoise.close_connections()


async def _clear_db() -> None:
    await Token.all().delete()
    await User.all().delete()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        asyncio.run(_clear_db())
        yield test_client
        asyncio.run(_clear_db())
