# recommendation_service/workers/recommendation_updater.py

import asyncio
from db.database import get_db
from repositories.analytics_repository import AnalyticsRepository


async def update_algorithm_weights():
    async with get_db() as db:
        await AnalyticsRepository.update_algorithm_weights(db)


async def main():
    while True:
        await update_algorithm_weights()
        await asyncio.sleep(3600)  # Обновлять каждую 1 час


if __name__ == "__main__":
    asyncio.run(main())
