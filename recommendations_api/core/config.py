import os

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
from pydantic_settings import BaseSettings

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    # Основные настройки проекта
    project_name: str = "recommendation_api"
    
    # Настройки базы данных
    MONGO_URL: str = Field("mongodb://mongodb:27017", env="MONGO_URL")
    DATABASE_NAME: str = Field("cinema", env="DATABASE_NAME")
    RECOMMENDATIONS_LIMITS: int = 3
    
    url_movies_search: str = "http://movie_api:8000/api/v1/films/"

    # Настройки Redis
    REDIS_URL: str = Field("redis://redis:6379/0", env="REDIS_URL")
    REDIS_CACHE_EXPIRE: int = 3600

    # Настройки Minio
    MINIO_ENDPOINT: str = Field("minio:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field("minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field("miniopassword", env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field("models", env="MINIO_BUCKET")

    # Настройки JWT
    secret_key: str = Field(
        "58ea1679ffb7715b56d0d3416850e89284331fc38fcf2963f5f26577bf1fac5b", 
        env="SECRET_KEY"
    )
    algorithm: str = Field("HS256", env="ALGORITHM")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DATABASE_NAME]
