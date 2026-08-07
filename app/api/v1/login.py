"""用户登录接口。"""

import uuid

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from tortoise.expressions import Q

from app.api.deps import _failure_response, token_check
from app.core.security import verify_password
from app.models import Token as TokenModel
from app.models import User as UserModel
from app.schemas import UserLoginRequest, UserLoginResponse, UserTokenRefreshRequest
from app.utils.time import utc_after

router = APIRouter(prefix="/login", tags=["auth"])


@router.post("/", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: UserLoginRequest) -> UserLoginResponse | JSONResponse:
    user = await UserModel.filter(
        Q(username=payload.username) | Q(phone=payload.username) | Q(email=payload.username)
    ).first()

    if not user:
        return _failure_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="LOGIN_FAILED",
            message="用户名或密码错误",
        )

    if not verify_password(payload.password, user.password):
        return _failure_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="LOGIN_FAILED",
            message="用户名或密码错误",
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


@router.put("/", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
@token_check(scope="*")
async def refresh_token(payload: UserTokenRefreshRequest, request: Request) -> UserLoginResponse | JSONResponse:
    token = request.state.current_token

    if token.refresh != payload.refresh:
        return _failure_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="REFRESH_TOKEN_INVALID",
            message="刷新令牌错误",
        )

    access_token = uuid.uuid4().hex
    refresh = uuid.uuid4().hex
    expires_at = utc_after(minutes=3)

    token.value = access_token
    token.refresh = refresh
    token.expire = expires_at
    await token.save()

    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh,
        expires_at=expires_at,
    )
