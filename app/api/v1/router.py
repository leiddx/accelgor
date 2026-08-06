"""v1 版本接口汇总入口，各业务模块的 router 在实现时 include 到此处。"""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")
