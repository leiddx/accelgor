"""异步并发数据聚合接口占位实现。"""

from fastapi import APIRouter, Query, Request, status

from app.api.deps import token_check

router = APIRouter(prefix="/aggregate", tags=["aggregate"])


@router.get("/", status_code=status.HTTP_200_OK)
@token_check(scope="*")
async def aggregate_placeholder(
    request: Request,
    n: int = Query(..., ge=1, le=100, description="占位任务数量，范围 1~100"),
) -> dict[str, int | str]:
    _ = request.state.current_token
    return {
        "message": "aggregate placeholder",
        "n": n,
    }