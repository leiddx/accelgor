"""二进制流图片上传接口。"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.api.deps import _failure_response, mime_type_check, token_check
from app.core.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_MIME_TYPES: dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
}


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
@token_check(scope="*")
@mime_type_check(ALLOWED_MIME_TYPES)
async def upload_image(request: Request) -> dict[str, str | int] | JSONResponse:
    mime_type = request.state.upload_mime_type
    extension = request.state.upload_extension

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}.{extension}"
    output_path = upload_dir / filename

    size = 0
    with output_path.open("wb") as output_file:
        async for chunk in request.stream():
            if not chunk:
                continue
            output_file.write(chunk)
            size += len(chunk)

    if size == 0:
        output_path.unlink(missing_ok=True)
        return _failure_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_EMPTY",
            message="上传内容为空",
        )

    return {
        "filename": filename,
        "mime_type": mime_type,
        "size": size,
    }
