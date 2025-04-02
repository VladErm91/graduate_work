# recommendation_service/ml/scheduler.py

from rq_scheduler import Scheduler
from core.redis import get_sync_redis
from recommendation_service.ml.tasks import update_all_recommendations, train_model
import asyncio


async def main():
    redis = get_sync_redis()
    scheduler = Scheduler(connection=redis)
    scheduler.cron(
        "0 0 * * *",  # Каждый день в 00:00
        train_model,
        id="train_model",
    )
    scheduler.cron(
        "30 0 * * *",  # Каждый день в 00:30
        update_all_recommendations,
        id="update_all_recommendations",
    )
    print(
        "Scheduler started, training model at 00:00, updating recommendations at 00:30"
    )

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
