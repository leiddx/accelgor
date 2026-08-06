from datetime import datetime, timedelta

import pytest
from tortoise import Tortoise

from app.models import Token, User


@pytest.mark.asyncio
async def test_user_and_token_models_can_be_created() -> None:
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    try:
        user = await User.create(
            username="alice",
            phone="13800000000",
            email="alice@example.com",
            password="hashed-password",
            salt="salt",
            scope="admin",
        )
        token = await Token.create(
            user=user,
            value="access-token",
            refresh="refresh-token",
            expire=datetime.now() + timedelta(hours=1),
            scope="admin",
        )

        assert user.id is not None
        assert token.user.id == user.id
    finally:
        await Tortoise.close_connections()
