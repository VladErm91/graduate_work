# recommendation_service/core/kafka.py

from confluent_kafka import Producer, Consumer
from core.config import settings

producer = Producer({"bootstrap.servers": settings.KAFKA_BROKER})

consumer = Consumer({
    "bootstrap.servers": settings.KAFKA_BROKER,
    "group.id": "recommendation_service",
    "auto.offset.reset": "earliest"
})
