"""密码哈希工具（bcrypt）。登录/鉴权的具体接口逻辑在对应功能中实现。"""

import bcrypt


def hash_password(plain_password: str, salt: str | bytes) -> str:
    salt_bytes = salt.encode("utf-8") if isinstance(salt, str) else salt
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt_bytes).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
