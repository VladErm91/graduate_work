# flask_kafka_app/app/kafka_producer.py
import json
import logging

from kafka import KafkaProducer

from .config import settings


def create_producer():
    return KafkaProducer(
        bootstrap_servers=f"{settings.host}:{settings.port}",
        value_serializer=lambda x: json.dumps(x).encode("utf-8"),
    )


def close_producer(producer):
    if producer:
        producer.close()
        logging.info("Kafka producer closed")
