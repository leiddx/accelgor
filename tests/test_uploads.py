from pathlib import Path
from io import BytesIO
import uuid

from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import settings


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def issue_user_token(client: TestClient) -> str:
    username = unique_username("upload_user")

    register_response = client.post(
        "/api/v1/users",
        json={"username": username, "password": "secret123"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/login",
        json={"username": username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def build_png_bytes(color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (1, 1), color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_image_requires_token(client: TestClient, tmp_path: Path) -> None:
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = str(tmp_path)

    try:
        response = client.post(
            "/api/v1/uploads",
            content=b"any-data",
            headers={"Content-Type": "image/png"},
        )

        assert response.status_code == 401
        assert response.json() == {
            "success": False,
            "code": "TOKEN_MISSING",
            "message": "缺少访问令牌",
        }
        assert list(tmp_path.iterdir()) == []
    finally:
        settings.UPLOAD_DIR = original_upload_dir


def test_upload_image_stream_save_success(client: TestClient, tmp_path: Path) -> None:
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = str(tmp_path)
    access_token = issue_user_token(client)

    try:
        image_bytes = build_png_bytes((12, 34, 56))
        response = client.post(
            "/api/v1/uploads",
            content=image_bytes,
            headers={
                "Content-Type": "image/png",
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["mime_type"] == "image/png"
        assert payload["filename"].endswith(".png")

        stored_file = tmp_path / payload["filename"]
        assert stored_file.exists()
        stored_bytes = stored_file.read_bytes()
        assert payload["size"] == len(stored_bytes)

        with Image.open(BytesIO(stored_bytes)) as stored_image:
            assert stored_image.convert("RGB").getpixel((0, 0)) == (56, 34, 12)
    finally:
        settings.UPLOAD_DIR = original_upload_dir


def test_upload_image_rejects_unsupported_mime(client: TestClient, tmp_path: Path) -> None:
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = str(tmp_path)
    access_token = issue_user_token(client)

    try:
        response = client.post(
            "/api/v1/uploads",
            content=b"not-an-image",
            headers={
                "Content-Type": "text/plain",
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 415
        assert response.json() == {
            "success": False,
            "code": "UNSUPPORTED_MEDIA_TYPE",
            "message": "仅支持 png 或 jpg/jpeg 图片",
        }
        assert list(tmp_path.iterdir()) == []
    finally:
        settings.UPLOAD_DIR = original_upload_dir


def test_upload_image_rejects_empty_body(client: TestClient, tmp_path: Path) -> None:
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = str(tmp_path)
    access_token = issue_user_token(client)

    try:
        response = client.post(
            "/api/v1/uploads",
            content=b"",
            headers={
                "Content-Type": "image/jpeg",
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 400
        assert response.json() == {
            "success": False,
            "code": "FILE_EMPTY",
            "message": "上传内容为空",
        }
        assert list(tmp_path.iterdir()) == []
    finally:
        settings.UPLOAD_DIR = original_upload_dir
