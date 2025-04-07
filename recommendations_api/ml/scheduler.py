# recommendation_service/scheduler.py
import asyncio
import logging
from rq_scheduler import Scheduler
from core.redis import get_sync_redis
from workers.tasks import train_model, update_all_recommendations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    redis = get_sync_redis()
    scheduler = Scheduler(connection=redis)

    # Очистка существующих задач (опционально)
    scheduler.cancel("full_train_model")
    scheduler.cancel("partial_train_model")
    scheduler.cancel("update_all_recommendations")

    # Задачи по расписанию
    scheduler.cron(
        "0 0 * * *",  # Каждый день в 00:00
        train_model,
        id="train_model",
    )
    scheduler.cron(
        "0 0 * * *",  # Каждый день в 00:00
        train_model,
        args=(False, True),  # Полное обучение с ALS
        id="full_train_model",
    )
    scheduler.cron(
        "*/15 * * * *",  # Каждые 15 минут
        train_model,
        args=(True, False),  # Частичное обучение без ALS
        id="partial_train_model",
    )
    scheduler.cron(
        "30 0 * * *",  # Каждый день в 00:30
        update_all_recommendations,
        id="update_all_recommendations",
    )
    logger.info(
        "Scheduler started: full training at 00:00, partial training every 15 mins, updating recs at 00:30"
    )

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
