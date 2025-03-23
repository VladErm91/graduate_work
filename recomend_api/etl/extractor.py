# ugc_sprint_1/etl/extractor.py
import json
import logging
from typing import Any, AsyncIterator

import backoff
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from configs.settings import KafkaSettings

logger = logging.getLogger("etl")

topics = ["click", "pageview", "quality_change", "filter_applied", "watched_time"]


class KafkaExtractor:
    def __init__(self, settings: KafkaSettings):
        self.consumer = AIOKafkaConsumer(
            topics[0],
            topics[1],
            topics[2],
            topics[3],
            topics[4],
            bootstrap_servers=f"{settings.host}:{settings.port}",
            auto_offset_reset="earliest",
            group_id=settings.group_id,
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

    @backoff.on_exception(
        backoff.expo,
        KafkaConnectionError,
        max_tries=10,
        max_time=10,
    )
    async def start(self) -> None:
        await self.consumer.start()

    async def close(self) -> None:
        await self.consumer.stop()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.consumer.commit()
        await self.close()

    @backoff.on_exception(
        backoff.expo,
        KafkaConnectionError,
        max_tries=10,
        max_time=10,
    )
    async def extract(self) -> AsyncIterator[dict[str, Any]]:
        try:
            data = await self.consumer.getmany(timeout_ms=2000)
        except KafkaError:
            logger.exception("ошибка при получении сообщений от kafka")
        if not data:
            logger.info("нет новых сообщений в kafka")
        for tp, messages in data.items():
            logger.info(
                f"Сообщение длинны {len(messages)} получено из топика: {tp.topic}"
            )
            for message in messages:
                logger.info(message.value)
                if message.value.get("event_type") in topics:
                    yield message.value  # Возврат только если тип соответствует
                else:
                    logger.warning(
                        f"Неизвестный тип события: {message.value.get('type')}"
                    )
