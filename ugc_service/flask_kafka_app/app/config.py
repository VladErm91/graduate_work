# ugc_sprint_1/flask_kafka_app/app/config.py

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = Field(default="kafka-0", alias="KAFKA_HOST")
    port: int = Field(default=9092, alias="KAFKA_API_PORT")


settings = Settings()
