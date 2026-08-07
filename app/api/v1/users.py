"""用户注册接口。"""

import bcrypt
from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import token_check
from app.core.security import hash_password
from app.models import User as UserModel
from app.schemas import UserCreate, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate) -> UserPublic:
    if await UserModel.filter(username=payload.username).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    if payload.phone and await UserModel.filter(phone=payload.phone).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="手机号已存在",
        )

    if payload.email and await UserModel.filter(email=payload.email).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已存在",
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