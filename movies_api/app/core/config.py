import os
from logging import config as logging_config

from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    project_name: str = "movies"

    # Настройки Redis
    redis_host: str = Field("127.0.0.1", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    # Настройки Elastic
    elastic_host: str = Field("127.0.0.1", alias="ELASTIC_HOST")
    elastic_port: int = Field(9200, alias="ELASTIC_PORT")
    elastic_schema: str = "http://"
    cache_time_life: int = 60 * 60

    # Tracing
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    jaeger_host: str = Field(default="jaeger", env="JAEGER_HOST")
    jaeger_port: int = Field(default=6831, env="JAEGER_UDP")

    # JWTAuthenticanion
    secret_key: str = Field(
        default=os.getenv(
            "SECRET_KEY",
            "58ea1679ffb7715b56d0d3416850e89284331fc38fcf2963f5f26577bf1fac5b",
        ),
        alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

settings = Settings()
