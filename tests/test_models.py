import pytest

from app.models import Token, User
from app.utils.time import utc_after


@pytest.mark.asyncio
async def test_user_and_token_models_can_be_created(initialized_tortoise: None) -> None:
    user = await User.create(
        username="alice_test_user_and_token_models_can_be_created",
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
        expire=utc_after(hours=1),
        scope="admin",
    )

    assert user.id is not None
    assert token.user.id == user.id
