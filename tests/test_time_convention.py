from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_DATETIME_NOW_FILES = {
    PROJECT_ROOT / "app" / "utils" / "time.py",
    PROJECT_ROOT / "tests" / "test_time_convention.py",
}


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for folder in ("app", "tests"):
        root = PROJECT_ROOT / folder
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            files.append(path)
    return files


def test_datetime_now_must_use_time_util() -> None:
    pattern = re.compile(r"\bdatetime\.now\(")
    violations: list[str] = []

    for path in _iter_python_files():
        if path in ALLOWED_DATETIME_NOW_FILES:
            continue

        content = path.read_text(encoding="utf-8")
        if pattern.search(content):
            violations.append(str(path.relative_to(PROJECT_ROOT)))

    assert not violations, (
        "禁止直接使用 datetime.now()，请改用 app.utils.time 中的统一方法。"
        f" 违规文件: {', '.join(violations)}"
    )
