import logging

import backoff
import clickhouse_connect
from clickhouse_connect.driver.exceptions import Error, OperationalError
from configs.settings import ClickhouseSettings
from models.event import EventMessage

logger = logging.getLogger("etl")


class ClickhouseLoader:
    def __init__(self, settings: ClickhouseSettings) -> None:
        self.settings = settings
        self.connect()

    @backoff.on_exception(
        backoff.expo,
        OperationalError,
        max_tries=10,
        max_time=10,
    )
    def connect(self):
        self.client = clickhouse_connect.get_client(
            host=self.settings.host,
            database=self.settings.database,
            username=self.settings.user,
            password=self.settings.password,
        )

    @backoff.on_exception(
        backoff.expo,
        OperationalError,
        max_tries=10,
        max_time=10,
    )
    async def load_batch(self, event_batch: list[EventMessage]):
        if not event_batch:
            return
        column_names = list(EventMessage.model_fields.keys())
        data = tuple(tuple(event.model_dump().values()) for event in event_batch)
        try:
            result = self.client.insert(
                table=self.settings.table, data=data, column_names=column_names
            )
        except Error:
            logger.exception(f"Ошибка загрузки данных в clickhouse {data}")
        else:
            logger.info(f"Загрузка блок {event_batch} с результатом {result.summary}")

    def close(self):
        if self.client:
            self.client.disconnect()
            self.client = None
            logger.debug("Разрыв соединения с Clickhouse")
