import sys
from functools import lru_cache
from typing import ClassVar

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
    )

    APP_NAME: str = "Webhook-Platform"
    APP_ENV: str = "DEVELOPMENT"
    DATABASE_URL: str = Field(min_length=1)
    DB_ECHO: bool = False
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_SIZE: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True

    JWT_ACCESS_SECRET: SecretStr = Field(min_length=64)
    JWT_ISSUER: str = Field(min_length=1)
    JWT_AUDIENCE: str = Field(min_length=1)

    REFRESH_TOKEN_PEPPER: SecretStr = Field(min_length=64)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    OPAQUE_TOKEN_PEPPER: str = Field(min_length=32)

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def REFRESH_TOKEN_KEY(self) -> str:
        app_name = self.APP_NAME.lower().replace("-", "_")
        return f"{app_name}session_refresh_token"


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()  # pyright: ignore[reportCallIssue]
    except ValidationError as exc:
        print("Application cannot start: invalid env configuration")
        print(exc)

        sys.exit(1)


settings = get_settings()
