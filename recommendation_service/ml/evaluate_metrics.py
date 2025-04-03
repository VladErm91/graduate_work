# recommendation_service/evaluate_metrics.py
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def calculate_metrics():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB_NAME]

    # Собираем все рекомендации и обратную связь
    recommendation_logs = await db["recommendation_logs"].find().to_list(None)
    feedback_logs = await db["feedback"].find().to_list(None)

    # Группируем обратную связь по session_id
    feedback_by_session = {}
    for fb in feedback_logs:
        session_id = fb["session_id"]
        if session_id not in feedback_by_session:
            feedback_by_session[session_id] = []
        feedback_by_session[session_id].append(
            {"movie_id": str(fb["movie_id"]), "liked": fb["liked"]}
        )

    # Вычисляем метрики
    als_precision, als_recall, als_count = 0, 0, 0
    lightfm_precision, lightfm_recall, lightfm_count = 0, 0, 0
    k = 3  # Precision@3 и Recall@3

    for rec in recommendation_logs:
        session_id = rec["session_id"]
        model_type = rec["model_type"]
        recommended = set(rec["recommendations"])
        feedback = feedback_by_session.get(session_id, [])

        if not feedback:
            continue

        liked = set(fb["movie_id"] for fb in feedback if fb["liked"])
        total_liked = len(liked)

        if not total_liked:
            continue

        # Precision@K
        relevant = len(recommended.intersection(liked))
        precision = relevant / min(k, len(recommended))

        # Recall@K
        recall = relevant / total_liked if total_liked > 0 else 0

        if model_type == "als":
            als_precision += precision
            als_recall += recall
            als_count += 1
        else:  # lightfm
            lightfm_precision += precision
            lightfm_recall += recall
            lightfm_count += 1

    # Средние значения
    als_precision = als_precision / als_count if als_count > 0 else 0
    als_recall = als_recall / als_count if als_count > 0 else 0
    lightfm_precision = lightfm_precision / lightfm_count if lightfm_count > 0 else 0
    lightfm_recall = lightfm_recall / lightfm_count if lightfm_count > 0 else 0

    logger.info(
        f"ALS Precision@3: {als_precision:.4f}, Recall@3: {als_recall:.4f}, Samples: {als_count}"
    )
    logger.info(
        f"LightFM Precision@3: {lightfm_precision:.4f}, Recall@3: {lightfm_recall:.4f}, Samples: {lightfm_count}"
    )


if __name__ == "__main__":
    asyncio.run(calculate_metrics())
