"""Tortoise ORM 连接配置。"""

from typing import Any

from app.core.config import settings

TORTOISE_ORM: dict[str, Any] = {
    "connections": {"default": settings.DB_URL},
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        },
    },
}
