"""应用配置，统一从环境变量 / .env 读取。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "accelgor"
    DEBUG: bool = False

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "accelgor"
    DB_PASSWORD: str = "accelgor"
    DB_NAME: str = "accelgor"
    # 显式设置时整体覆盖上面几项拼出的连接串，供测试环境切换为 sqlite 等场景使用
    DATABASE_URL: str | None = None

    UPLOAD_DIR: str = "uploads"

    @property
    def DB_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
