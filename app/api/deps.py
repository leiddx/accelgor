"""跨接口共享的依赖项（如登录态校验）。"""

from collections.abc import Awaitable, Callable
from datetime import timezone
from functools import wraps
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.models import Token as TokenModel
from app.utils.time import utc_now


def _failure_response(status_code: int, code: str, message: str) -> JSONResponse:
	return JSONResponse(
		status_code=status_code,
		content={
			"success": False,
			"code": code,
			"message": message,
		},
	)


def _extract_token_value(request: Request) -> str:
	auth_header = request.headers.get("Authorization", "").strip()
	if auth_header.lower().startswith("bearer "):
		return auth_header[7:].strip()

	for header_name in ("X-Token", "token"):
		value = request.headers.get(header_name, "").strip()
		if value:
			return value

	return ""


def _split_scopes(raw_scope: str) -> set[str]:
	return {item for item in raw_scope.replace(",", " ").split() if item}


def _has_scope(granted_scope: str, required_scope: str) -> bool:
	if required_scope == "*":
		return True

	required = _split_scopes(required_scope)
	if not required:
		return True

	granted = _split_scopes(granted_scope)
	if "*" in granted:
		return True

	return required.issubset(granted)


def _resolve_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request | None:
	request = kwargs.get("request")
	if isinstance(request, Request):
		return request

	for arg in args:
		if isinstance(arg, Request):
			return arg

	return None


def token_check(scope: str) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
	"""校验请求头 token 的有效性和权限范围。"""

	def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
		@wraps(func)
		async def wrapper(*args: Any, **kwargs: Any) -> Any:
			request = _resolve_request(args, kwargs)
			if request is None:
				return _failure_response(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
					code="REQUEST_CONTEXT_MISSING",
					message="请求上下文缺失",
				)

			token_value = _extract_token_value(request)
			if not token_value:
				return _failure_response(
					status_code=status.HTTP_401_UNAUTHORIZED,
					code="TOKEN_MISSING",
					message="缺少访问令牌",
				)

			token = await TokenModel.filter(value=token_value).first()
			if token is None:
				return _failure_response(
					status_code=status.HTTP_401_UNAUTHORIZED,
					code="TOKEN_INVALID",
					message="访问令牌无效",
				)

			token_expire = token.expire
			if token_expire.tzinfo is None:
				token_expire = token_expire.replace(tzinfo=timezone.utc)

			if token_expire <= utc_now():
				return _failure_response(
					status_code=status.HTTP_401_UNAUTHORIZED,
					code="TOKEN_EXPIRED",
					message="访问令牌已过期",
				)

			if not _has_scope(token.scope, scope):
				return _failure_response(
					status_code=status.HTTP_403_FORBIDDEN,
					code="SCOPE_FORBIDDEN",
					message="权限范围不足",
				)

			request.state.current_token = token

			return await func(*args, **kwargs)

		return wrapper

	return decorator
