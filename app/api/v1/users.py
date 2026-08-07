"""用户注册接口。"""

import bcrypt
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.api.deps import _failure_response, token_check
from app.core.security import hash_password
from app.models import User as UserModel
from app.schemas import UserCreate, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate) -> UserPublic | JSONResponse:
    if await UserModel.filter(username=payload.username).exists():
        return _failure_response(
            status_code=status.HTTP_409_CONFLICT,
            code="USERNAME_CONFLICT",
            message="用户名已存在",
        )

    if payload.phone and await UserModel.filter(phone=payload.phone).exists():
        return _failure_response(
            status_code=status.HTTP_409_CONFLICT,
            code="PHONE_CONFLICT",
            message="手机号已存在",
        )

    if payload.email and await UserModel.filter(email=payload.email).exists():
        return _failure_response(
            status_code=status.HTTP_409_CONFLICT,
            code="EMAIL_CONFLICT",
            message="邮箱已存在",
        )

    salt = bcrypt.gensalt()
    user = await UserModel.create(
        username=payload.username,
        phone=payload.phone or "",
        email=payload.email or "",
        password=hash_password(payload.password, salt),
        salt=salt.decode("utf-8"),
        scope="user",
    )

    return UserPublic.model_validate(user)


@router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
@token_check(scope="user")
async def get_current_user(request: Request) -> UserPublic:
    token = request.state.current_token
    user = await UserModel.get(id=token.user_id)
    return UserPublic.model_validate(user)


@router.get("/admin/ping", status_code=status.HTTP_200_OK)
@token_check(scope="admin")
async def admin_ping(request: Request) -> dict[str, str]:
    _ = request.state.current_token
    return {"status": "ok"}