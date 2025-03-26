# recommendation_service/repositories/analytics_repository.py

from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsRepository:
    @staticmethod
    async def log_interaction(
        user_id: str,
        algorithm: str,
        recommended: list,
        clicked: list,
        watched: list,
        completed: list,
        db: AsyncSession,
    ):
        """Сохраняем пользовательские действия для анализа эффективности рекомендаций"""
        query = """
        INSERT INTO recommendation_metrics (user_id, algorithm, recommended_movies, clicked_movies, watched_movies, completed_movies, timestamp)
        VALUES (:user_id, :algorithm, :recommended_movies, :clicked_movies, :watched_movies, :completed_movies, now())
        """
        await db.execute(
            query,
            {
                "user_id": user_id,
                "algorithm": algorithm,
                "recommended_movies": recommended,
                "clicked_movies": clicked,
                "watched_movies": watched,
                "completed_movies": completed,
            },
        )
        await db.commit()

    @staticmethod
    async def update_algorithm_weights(db: AsyncSession):
        """Обновляет веса алгоритмов на основе метрик"""
        ctr_query = """
        SELECT algorithm, avg(length(clicked_movies) / length(recommended_movies)) AS CTR
        FROM recommendation_metrics
        GROUP BY algorithm
        """
        result = await db.execute(ctr_query)
        ctr_data = dict(result.fetchall())  # {"A": 0.12, "B": 0.08}

        total_ctr = sum(ctr_data.values())
        if total_ctr > 0:
            new_weights = {alg: ctr / total_ctr for alg, ctr in ctr_data.items()}
        else:
            new_weights = {
                "A": 0.5,
                "B": 0.5,
            }  # Восстанавливаем баланс, если нет данных

        for algorithm, weight in new_weights.items():
            await db.execute(
                "UPDATE algorithm_weights SET weight = :weight WHERE algorithm = :algorithm",
                {"algorithm": algorithm, "weight": weight},
            )
        await db.commit()
