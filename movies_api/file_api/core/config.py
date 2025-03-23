import os
from logging import config as logging_config

from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    project_name: str = "File API"

    # db
    db_name: str = Field(default="movies_database", alias="DB_NAME")
    db_user: str = Field(default="app", alias="DB_USER")
    db_password: str = Field(default="123qwe", alias="DB_PASSWORD")
    db_host: str = Field(default="127.0.0.1", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")

    # minio
    minio_host: str = Field(default="127.0.0.1", alias="MINIO_HOST")
    minio_root_user: str = Field(default="practicum", alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(default="StrongPass", alias="MINIO_ROOT_PASSWORD")
    bucket_name: str = Field(default="movies", alias="BUCKET_NAME")

    def get_url(self) -> str:
        db_url = f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return db_url

    class Config:
        env_file = ".env"


# Создаем экземпляр класса Settings для хранения настроек
settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
