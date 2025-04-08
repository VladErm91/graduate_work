import os

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
from pydantic_settings import BaseSettings

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    project_name: str = "recommendation_api"

    # Настройки базы данных
    MONGO_URL: str = "mongodb://mongodb:27017"
    DATABASE_NAME: str = "cinema"
    RECOMMENDATIONS_LIMITS: int = 3

    url_movies_search: str = "http://movie_api:8000/api/v1/films/"

    # Настройки Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_CACHE_EXPIRE: int = 3600

    # Настройки Minio
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "miniopassword"
    MINIO_BUCKET: str = "models"

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


settings = Settings()

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DATABASE_NAME]
