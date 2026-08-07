"""用户登录接口。"""

import uuid

from fastapi import APIRouter, HTTPException, status
from tortoise.expressions import Q

from app.core.security import verify_password
from app.models import Token as TokenModel
from app.models import User as UserModel
from app.schemas import UserLoginRequest, UserLoginResponse
from app.utils.time import utc_after

router = APIRouter(prefix="/login", tags=["auth"])


@router.post("/", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: UserLoginRequest) -> UserLoginResponse:
    user = await UserModel.filter(
        Q(username=payload.username) | Q(phone=payload.username) | Q(email=payload.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token = uuid.uuid4().hex
    refresh_token = uuid.uuid4().hex
    expires_at = utc_after(minutes=3)

    await TokenModel.create(
        value=access_token,
        refresh=refresh_token,
        expire=expires_at,
        user=user,
        scope=user.scope,
    )

    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )
