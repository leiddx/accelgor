"""跨接口共享的依赖项（如登录态校验）。"""

from collections.abc import Awaitable, Callable, Mapping
from datetime import timezone
from functools import wraps
from io import BytesIO
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

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


def mime_type_check(
	allowed_mime_types: Mapping[str, str],
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
	"""校验 Content-Type，并写入 request.state 供业务函数复用。"""

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

			raw_content_type = request.headers.get("Content-Type", "")
			mime_type = raw_content_type.split(";", 1)[0].strip().lower()

			if not mime_type:
				return _failure_response(
					status_code=status.HTTP_400_BAD_REQUEST,
					code="MIME_TYPE_MISSING",
					message="缺少 Content-Type 请求头",
				)

			extension = allowed_mime_types.get(mime_type)
			if extension is None:
				return _failure_response(
					status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
					code="UNSUPPORTED_MEDIA_TYPE",
					message="仅支持 png 或 jpg/jpeg 图片",
				)

			request.state.upload_mime_type = mime_type
			request.state.upload_extension = extension

			return await func(*args, **kwargs)

		return wrapper

	return decorator


def swap_rgb_to_bgr() -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
	"""将上传图片的 RGB 通道转换为 BGR，并写入 request.state。"""

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

			raw_chunks: list[bytes] = []
			async for chunk in request.stream():
				if chunk:
					raw_chunks.append(chunk)

			raw_bytes = b"".join(raw_chunks)
			if not raw_bytes:
				request.state.transformed_upload_bytes = b""
				return await func(*args, **kwargs)

			mime_type = getattr(request.state, "upload_mime_type", "")

			try:
				with Image.open(BytesIO(raw_bytes)) as image:
					if mime_type == "image/png" and "A" in image.getbands():
						r, g, b, a = image.convert("RGBA").split()
						converted = Image.merge("RGBA", (b, g, r, a))
						output_format = "PNG"
					elif mime_type == "image/png":
						r, g, b = image.convert("RGB").split()
						converted = Image.merge("RGB", (b, g, r))
						output_format = "PNG"
					else:
						r, g, b = image.convert("RGB").split()
						converted = Image.merge("RGB", (b, g, r))
						output_format = "JPEG"

					output_buffer = BytesIO()
					converted.save(output_buffer, format=output_format)
					request.state.transformed_upload_bytes = output_buffer.getvalue()
			except (UnidentifiedImageError, OSError):
				return _failure_response(
					status_code=status.HTTP_400_BAD_REQUEST,
					code="IMAGE_INVALID",
					message="上传内容不是有效图片",
				)

			return await func(*args, **kwargs)

		return wrapper

	return decorator
