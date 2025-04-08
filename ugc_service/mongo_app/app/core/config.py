import os

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "rating_review_service"
    MONGO_URL: str = "mongodb://mongodb:27017"
    DATABASE_NAME: str = "cinema"
    sentry_dsn: str = ""

    # JWTAuthenticanion
    secret_key: str = Field(
        default=os.getenv(
            "SECRET_KEY",
            "58ea1679ffb7715b56d0d3416850e89284331fc38fcf2963f5f26577bf1fac5b",
        ),
        alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")

    # Logger
    log_level: str = "INFO"
    logger_filename: str = log_level + ".log"
    logger_maxbytes: int = 1500000
    logger_mod: str = "a"
    logger_backup_count: int = 3


settings = Settings()


client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DATABASE_NAME]
