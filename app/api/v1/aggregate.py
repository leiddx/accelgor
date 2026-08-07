"""异步并发数据聚合接口占位实现。"""

import asyncio
import math
import random
import time
from typing import Any

from fastapi import APIRouter, Query, Request, status

from app.api.deps import token_check

router = APIRouter(prefix="/aggregate", tags=["aggregate"])


async def simulate_cpu_intensive_task(
    min_seconds: int = 1,
    max_seconds: int = 10,
    timeout_seconds: float | None = None,
    error_probability: float = 0.1,
) -> int:
    """模拟随机时长的 CPU 密集型任务，按概率随机抛出异常。"""
    if min_seconds <= 0 or max_seconds <= 0:
        raise ValueError("min_seconds and max_seconds must be positive")
    if min_seconds > max_seconds:
        raise ValueError("min_seconds cannot be greater than max_seconds")
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if error_probability < 0 or error_probability > 1:
        raise ValueError("error_probability must be between 0 and 1")

    if random.random() < error_probability:
        raise RuntimeError("simulated random cpu task error")

    duration_seconds = random.randint(min_seconds, max_seconds)
    end_time = time.perf_counter() + duration_seconds

    def _burn_cpu_until(deadline: float) -> float:
        # 持续执行数学计算，模拟 CPU 密集型工作负载。
        accumulator = 0.0
        while time.perf_counter() < deadline:
            accumulator = math.sqrt(accumulator + 1.23456789)
        return accumulator

    cpu_task = asyncio.to_thread(_burn_cpu_until, end_time)
    if timeout_seconds is None:
        await cpu_task
    else:
        await asyncio.wait_for(cpu_task, timeout=timeout_seconds)

    return duration_seconds


async def _run_single_aggregate_task(
    task_id: int,
    semaphore: asyncio.Semaphore,
    cpu_timeout_seconds: float,
) -> dict[str, Any]:
    """执行单个聚合任务：先模拟 I/O，再模拟 CPU 计算。"""
    started_at = time.perf_counter()
    async with semaphore:
        io_delay_seconds = round(random.uniform(0.1, 0.3), 3)
        await asyncio.sleep(io_delay_seconds)
        cpu_duration_seconds = await simulate_cpu_intensive_task(timeout_seconds=cpu_timeout_seconds)

    elapsed_seconds = round(time.perf_counter() - started_at, 3)
    return {
        "task_id": task_id,
        "status": "success",
        "io_delay_seconds": io_delay_seconds,
        "cpu_duration_seconds": cpu_duration_seconds,
        "elapsed_seconds": elapsed_seconds,
    }


@router.get("/", status_code=status.HTTP_200_OK)
@token_check(scope="*")
async def aggregate(
    request: Request,
    n: int = Query(..., ge=1, le=100, description="并发任务数量，范围 1~100"),
    max_concurrency: int = Query(3, ge=1, le=10, description="最大并发数，范围 1~10"),
    cpu_timeout_seconds: float = Query(12.0, gt=0, le=30, description="单任务 CPU 超时时间（秒）"),
) -> dict[str, Any]:
    _ = request.state.current_token
    semaphore = asyncio.Semaphore(min(n, max_concurrency))

    started_at = time.perf_counter()
    tasks = [
        _run_single_aggregate_task(
            task_id=index + 1,
            semaphore=semaphore,
            cpu_timeout_seconds=cpu_timeout_seconds,
        )
        for index in range(n)
    ]
    gathered_results = await asyncio.gather(*tasks, return_exceptions=True)
    total_elapsed_seconds = round(time.perf_counter() - started_at, 3)

    results: list[dict[str, Any]] = []
    for index, item in enumerate(gathered_results, start=1):
        if isinstance(item, BaseException):
            results.append(
                {
                    "task_id": index,
                    "status": "failed",
                    "error_type": type(item).__name__,
                    "error": str(item) or "task failed",
                }
            )
            continue

        results.append(item)

    success_count = sum(1 for item in results if item.get("status") == "success")
    failed_count = n - success_count

    return {
        "message": "aggregate completed",
        "n": n,
        "max_concurrency": min(n, max_concurrency),
        "success_count": success_count,
        "failed_count": failed_count,
        "total_elapsed_seconds": total_elapsed_seconds,
        "results": results,
    }