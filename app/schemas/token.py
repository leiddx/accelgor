from datetime import datetime
from pydantic import BaseModel, Field

from .user import User


class Token(BaseModel):
    """令牌"""

    id: int = Field(..., description="令牌记录 ID")

    user: User = Field(..., description="关联用户信息")

    value: str = Field(
        ..., description="访问令牌值", json_schema_extra={"x-index": True}
    )
    refresh: str = Field(
        ..., description="刷新令牌值", json_schema_extra={"x-index": True}
    )
    expire: datetime = Field(..., description="令牌过期时间")
    scope: str = Field(..., description="令牌授权范围")

    created: datetime = Field(..., description="创建时间")
    updated: datetime = Field(..., description="更新时间")