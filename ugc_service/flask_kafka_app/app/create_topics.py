# ugc_sprint_1/flask_kafka_app/app/create_topics.py
import logging

from kafka.admin import KafkaAdminClient, NewTopic

from .config import settings

TOPICS = ["click", "pageview", "quality_change", "filter_applied", "watched_time"]


def create_topics_if_not_exists():
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=f"{settings.host}:{settings.port}",
            client_id="flask_topic_creator",
        )

        # Проверка существующих топиков
        existing_topics = admin_client.list_topics()
        topics_to_create = [
            NewTopic(name=topic, num_partitions=1, replication_factor=1)
            for topic in TOPICS
            if topic not in existing_topics
        ]

        # Создание топиков при их отсутствии
        if topics_to_create:
            admin_client.create_topics(new_topics=topics_to_create, validate_only=False)
            logging.info(
                f"Topics created: {[topic.name for topic in topics_to_create]}"
            )
        else:
            logging.info("All topics already exist, no topics created.")

    except Exception as e:
        logging.error(f"Failed to create topics: {e}")
    finally:
        admin_client.close()
