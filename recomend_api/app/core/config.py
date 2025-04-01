import os
from logging import config as logging_config

from core.logger import LOGGING
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
from pydantic_settings import BaseSettings

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    project_name: str = "recomend_api"

    # db
    db_name: str = Field(default="movies_database", alias="DB_NAME")
    db_user: str = Field(default="app", alias="DB_USER")
    db_password: str = Field(default="123qwe", alias="DB_PASSWORD")
    db_host: str = Field(default="127.0.0.1", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")

    # Настройки базы данных
    MONGO_URL: str = "mongodb://mongodb:27017"
    url_movies_search: str = "http://movie_api:8000/api/v1/films/"
    url_movies_id: str = "http://movie_api:8000/api/v1/films/{film_uuid}"
    ML_SERVICE = "ml-service:8060"

    DATABASE_NAME: str = "cinema"

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

    def get_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

settings = Settings()

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DATABASE_NAME]
