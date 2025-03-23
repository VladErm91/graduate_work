# flask_kafka_app/app/event_generator.py
import argparse
import asyncio
import logging
import random
import uuid
from datetime import datetime

import httpx

API_URL = "http://localhost:8000/v1"  # URL приложения Flask
USER_IDS = [
    "8e9e106e-ad52-479c-8e2c-a2cb7dee5a07",
    "8147aede-0457-4283-bd0f-880536bac87d",
    "2c28b60f-2fc5-456b-ba4a-dd7bb9d2c05b",
]
EVENT_TYPES = ["click", "pageview", "quality_change", "filter_applied", "watched_time"]
FILM_IDS = [str(uuid.uuid4()) for _ in range(3)]
FILM_QUALITIES = [1080, 720, 480]
ELEMENTS = ["button", "input", "link"]
logging.basicConfig(level=logging.INFO)


async def send_event(event_type):
    """Отправка события"""
    data = {
        "user_id": random.choice(USER_IDS),
        "event_type": event_type,
        "timestamp": datetime.now().isoformat() + "Z",
        "fingerprint": "dummy_fingerprint",
    }

    if event_type == "click":
        data["element"] = random.choice(ELEMENTS)
        data["page_url"] = "https://example.com/page"
    elif event_type == "pageview":
        data["page_url"] = "https://example.com/page"
    elif event_type == "quality_change":
        data["id_film"] = random.choice(FILM_IDS)
        data["film"] = "Dummy Film"
        data["original_quality"] = random.choice(FILM_QUALITIES)
        data["updated_quality"] = random.choice(FILM_QUALITIES)
    elif event_type == "filter_applied":
        data["filter"] = "Dummy Filter"
    elif event_type == "watched_time":
        data["id_film"] = random.choice(FILM_IDS)
        data["film"] = "Dummy Film"
        data["time"] = random.randint(1, 100)

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/track_event", json=data)
        if response.status_code == 200:
            logging.info(f"Click event sent: {data}")
        else:
            logging.error(f"Failed to send click event: {response.text}")


async def main(event_count):
    """Основной цикл генерации событий"""
    for _ in range(event_count):
        event_type = random.choice(EVENT_TYPES)
        await send_event(event_type)
        await asyncio.sleep(random.uniform(1, 3))  # Задержка между отправками


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Event generator for Kafka API")
    parser.add_argument(
        "--event-count", type=int, default=10, help="Количество событий для отправки"
    )
    args = parser.parse_args()

    asyncio.run(main(args.event_count))
