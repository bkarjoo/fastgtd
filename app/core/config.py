from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "fastgtd"
    env: str = "development"
    database_url: str

    # Auth/JWT
    jwt_secret: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 1440
    jwt_algorithm: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
