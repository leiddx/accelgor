"""统一时间处理工具（UTC）。"""

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    """返回带时区的 UTC 当前时间。"""
    return datetime.now(timezone.utc)


def utc_after(**delta_kwargs: int) -> datetime:
    """返回 UTC 当前时间之后的时间点。"""
    return utc_now() + timedelta(**delta_kwargs)


def utc_before(**delta_kwargs: int) -> datetime:
    """返回 UTC 当前时间之前的时间点。"""
    return utc_now() - timedelta(**delta_kwargs)
