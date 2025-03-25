from db.redis import redis_client
from db.database import get_db
from repositories.algorithms import AlgorithmA, AlgorithmB


class RecommendationRepository:
    @staticmethod
    async def get_recommendations(user_id: str, db):
        cache_key = f"user_recommendations:{user_id}"
        cached_recommendations = await redis_client.get(cache_key)

        if cached_recommendations:
            return cached_recommendations.decode("utf-8").split(",")

        algorithm = await db.execute(
            "SELECT algorithm FROM user_algorithms WHERE user_id = :user_id",
            {"user_id": user_id},
        )
        algorithm = algorithm.scalar()

        if algorithm == "A":
            recommendations = await AlgorithmA.get_recommendations(user_id, db)
        else:
            recommendations = await AlgorithmB.get_recommendations(user_id, db)

        await redis_client.set(
            cache_key, ",".join(recommendations), ex=3600
        )  # Кешируем на 1 час
        return recommendations
