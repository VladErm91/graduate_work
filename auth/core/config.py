import os
from logging import config as logging_config

from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict


# Минимальная длина пароля для повышения безопасности
MIN_PASSWORD_LENGTH = 8

DEVICES = ["web", "mobile", "smart"]

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ProviderSettings(BaseSettings):
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    auth_url: str
    token_url: str
    user_info_url: str
    api_version: str = "5.131"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__"
    )
    project_name: str = "auth"

    # db
    db_name: str = Field(default="movies_database", alias="DB_NAME")
    db_user: str = Field(default="app", alias="DB_USER")
    db_password: str = Field(default="123qwe", alias="DB_PASSWORD")
    db_host: str = Field(default="127.0.0.1", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")

    # Настройки Redis
    redis_host: str = Field("127.0.0.1", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    # Настройки JWT
    # to get a string like this run:
    # openssl rand -hex 32
    secret_key: str = Field(
        default=os.getenv(
            "SECRET_KEY",
            "58ea1679ffb7715b56d0d3416850e89284331fc38fcf2963f5f26577bf1fac5b",
        ),
        alias="SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=30,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    refresh_token_expire_days: int = Field(
        default=30,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")

    def get_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Tracing
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    jaeger_host: str = Field(default="jaeger", env="JAEGER_HOST")
    jaeger_port: int = Field(default=6831, env="JAEGER_UDP")
    request_limit_per_minute: int = 20

    providers: Dict[str, ProviderSettings]

    # class Config:
    #     env_file = ".env"


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

settings = Settings()
