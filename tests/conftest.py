"""测试环境固定使用内存 sqlite，避免依赖真实 MySQL 实例，需在导入 app 前设置。"""

import os
import asyncio
import pytest
import pytest_asyncio

from tortoise import Tortoise
from fastapi.testclient import TestClient
from collections.abc import AsyncGenerator, Generator

TEST_DB_URL = "sqlite://tests/test.sqlite3"

os.environ["DATABASE_URL"] = TEST_DB_URL

# os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")
# os.environ.setdefault("DEBUG", "true")

from app.main import app
from app.models import Token, User


@pytest_asyncio.fixture()
async def initialized_tortoise() -> AsyncGenerator[None, None]:
    await Tortoise.init(
        db_url=TEST_DB_URL,
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
        # 先触发一次请求，确保 register_tortoise 的初始化与建表完成
        test_client.get("/health")
        asyncio.run(_clear_db())
        yield test_client
        asyncio.run(_clear_db())
