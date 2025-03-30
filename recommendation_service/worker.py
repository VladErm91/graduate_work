# recommendation_service/worker.py

import asyncio
from core.kafka_utils import get_consumer
from tasks import get_queue, update_recommendations


async def process_message(message):
    data = message.value
    user_id = data["user_id"]
    queue = await get_queue()
    queue.enqueue(update_recommendations, user_id)


async def main():
    consumer = get_consumer("user_history", "recommendation_worker")
    print("Kafka worker started, listening to 'user_history' topic...")
    for message in consumer:
        await process_message(message)


if __name__ == "__main__":
    asyncio.run(main())
