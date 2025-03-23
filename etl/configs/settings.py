# ugc_sprint_1/etl/configs/settings.py
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class KafkaSettings(BaseModel):
    host: str = Field(default="kafka-0", alias="KAFKA_HOST")
    port: int = Field(default=9092, alias="KAFKA_PORT")
    group_id: str = "click_events"


class Settings(BaseSettings):

    log_level: str = "info"
    batch_size: int = 10000
    run_interval_seconds: int = 5
    kafkasettings: KafkaSettings = KafkaSettings()

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=BASE_DIR / ".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
    )


settings = Settings()
