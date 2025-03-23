import asyncio
from aiokafka import AIOKafkaConsumer
from core.database import get_db
from services.hybrid_recommender import HybridRecommender


async def consume():
    consumer = AIOKafkaConsumer(
        "recommendations", bootstrap_servers="kafka:9092", group_id="recommender"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            user_id = msg.value.decode("utf-8")
            async with get_db() as db:
                recommender = HybridRecommender()
                await recommender.get_hybrid_recommendations(user_id, db)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume())
