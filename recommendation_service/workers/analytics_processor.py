import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from repositories.analytics_repository import AnalyticsRepository


async def process_metrics():
    """Обновляет метрики каждые 10 минут"""
    while True:
        async with get_db() as db:
            ctr = await db.execute(
                "SELECT algorithm, avg(length(clicked_movies) / length(recommended_movies)) FROM recommendation_metrics GROUP BY algorithm"
            )
            engagement = await db.execute(
                "SELECT algorithm, avg(length(watched_movies) / length(recommended_movies)) FROM recommendation_metrics GROUP BY algorithm"
            )
            conversion = await db.execute(
                "SELECT algorithm, avg(length(completed_movies) / length(watched_movies)) FROM recommendation_metrics GROUP BY algorithm"
            )

            print(
                f"CTR: {ctr.fetchall()}, Engagement: {engagement.fetchall()}, Conversion: {conversion.fetchall()}"
            )

        await asyncio.sleep(600)  # Запускаем каждые 10 минут


if __name__ == "__main__":
    asyncio.run(process_metrics())
