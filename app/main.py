"""FastAPI 应用入口。"""

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.tortoise_config import TORTOISE_ORM

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.include_router(api_router)

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=False,
    add_exception_handlers=True,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
