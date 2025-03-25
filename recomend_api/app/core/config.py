import os
from typing import Dict
from logging import config as logging_config

from core.logger import LOGGING

from pydantic import Field
from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    project_name: str = "auth"

    # Настройки базы данных
    MONGO_URL: str = "mongodb://mongodb:27017"
    DATABASE_NAME: str = "cinema"
    sentry_dsn: str = ""

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
    algorithm: str = Field(default="HS256", alias="ALGORITHM")

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

settings = Settings()

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DATABASE_NAME]
