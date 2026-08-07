"""Hello World 鉴权接口。"""

from fastapi import APIRouter, Request, status

from app.api.deps import token_check

router = APIRouter(prefix="/hello", tags=["hello"])


@router.get("/user", status_code=status.HTTP_200_OK)
@token_check(scope="user")
async def hello_user(request: Request) -> str:
    _ = request.state.current_token
    return "Hello World"


@router.get("/admin", status_code=status.HTTP_200_OK)
@token_check(scope="admin")
async def hello_admin(request: Request) -> str:
    _ = request.state.current_token
    return "Hello World"
