from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class User(BaseModel):
    """用户信息"""

    id: int = Field(..., description="用户 ID")

    username: str = Field(
        ..., description="用户名", json_schema_extra={"x-index": True}
    )
    phone: str | None = Field(
        None, description="手机号", json_schema_extra={"x-index": True}
    )
    email: str | None = Field(
        None, description="邮箱", json_schema_extra={"x-index": True}
    )

    password: str = Field(
        ..., description="密码哈希值", json_schema_extra={"x-index": True}
    )
    salt: str | None = Field(
        None, description="密码盐值", json_schema_extra={"x-index": True}
    )


    scope: str = Field(..., description="用户权限范围")

    created: datetime = Field(..., description="创建时间")
    updated: datetime = Field(..., description="更新时间")


class UserCreate(BaseModel):
    """用户注册请求。"""

    username: str = Field(..., min_length=1, max_length=64, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    phone: str | None = Field(None, max_length=20, description="手机号")
    email: str | None = Field(None, max_length=255, description="邮箱")

    @field_validator("username", "password")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value

    @field_validator("phone", "email")
    @classmethod
    def normalize_optional(cls, value: str | None) -> str | None:
        if value is None:
            return ""
        value = value.strip()
        return value


class UserLoginRequest(BaseModel):
    """用户登录请求。"""

    username: str = Field(..., min_length=1, description="登录账号，可匹配用户名/手机号/邮箱")
    password: str = Field(..., min_length=1, description="密码")

    @field_validator("username", "password")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value


class UserLoginResponse(BaseModel):
    """用户登录响应。"""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    expires_at: datetime = Field(..., description="过期时间")


class UserTokenRefreshRequest(BaseModel):
    """刷新访问令牌请求。"""

    refresh: str = Field(..., min_length=1, description="刷新令牌")

    @field_validator("refresh")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value


class UserPublic(BaseModel):
    """对外返回的用户信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    phone: str | None = Field(None, description="手机号")
    email: str | None = Field(None, description="邮箱")
    scope: str = Field(..., description="用户权限范围")
    created: datetime = Field(..., description="创建时间")
    updated: datetime = Field(..., description="更新时间")