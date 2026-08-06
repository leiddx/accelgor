from datetime import datetime
from pydantic import BaseModel, Field


class User(BaseModel):
    """用户信息"""

    id: int = Field(..., description="用户 ID")

    username: str = Field(
        ..., description="用户名", json_schema_extra={"x-index": True}
    )
    phone: str = Field(
        ..., description="手机号", json_schema_extra={"x-index": True}
    )
    email: str = Field(
        ..., description="邮箱", json_schema_extra={"x-index": True}
    )

    password: str = Field(
        ..., description="密码哈希值", json_schema_extra={"x-index": True}
    )
    salt: str = Field(
        ..., description="密码盐值", json_schema_extra={"x-index": True}
    )


    scope: str = Field(..., description="用户权限范围")

    created: datetime = Field(..., description="创建时间")
    updated: datetime = Field(..., description="更新时间")