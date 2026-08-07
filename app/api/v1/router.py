"""v1 版本接口汇总入口，各业务模块的 router 在实现时 include 到此处。"""

from fastapi import APIRouter

from app.api.v1.hello import router as hello_router
from app.api.v1.login import router as login_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users_router)
api_router.include_router(login_router)
api_router.include_router(hello_router)
api_router.include_router(uploads_router)
