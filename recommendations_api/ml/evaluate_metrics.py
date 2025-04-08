# recommendations_api/ml/evaluate_metrics.py


import asyncio
import logging
from prometheus_client import Gauge, start_http_server

from core.config import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Метрики Prometheus
ALS_PRECISION = Gauge('als_precision_at_3', 'Precision@3 for ALS model')
ALS_RECALL = Gauge('als_recall_at_3', 'Recall@3 for ALS model')
ALS_SAMPLES = Gauge('als_samples', 'Number of ALS samples evaluated')
LIGHTFM_PRECISION = Gauge('lightfm_precision_at_3', 'Precision@3 for LightFM model')
LIGHTFM_RECALL = Gauge('lightfm_recall_at_3', 'Recall@3 for LightFM model')
LIGHTFM_SAMPLES = Gauge('lightfm_samples', 'Number of LightFM samples evaluated')


async def calculate_metrics():

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
        model_type = model_type = rec.get("source", rec.get("model_type", "unknown"))  # Используем source, с fallback на model_type
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
        # Игнорируем "popular" или другие значения source

    # Средние значения
    als_precision = als_precision / als_count if als_count > 0 else 0
    als_recall = als_recall / als_count if als_count > 0 else 0
    lightfm_precision = lightfm_precision / lightfm_count if lightfm_count > 0 else 0
    lightfm_recall = lightfm_recall / lightfm_count if lightfm_count > 0 else 0

    # Обновляем метрики Prometheus
    ALS_PRECISION.set(als_precision)
    ALS_RECALL.set(als_recall)
    ALS_SAMPLES.set(als_count)
    LIGHTFM_PRECISION.set(lightfm_precision)
    LIGHTFM_RECALL.set(lightfm_recall)
    LIGHTFM_SAMPLES.set(lightfm_count)

    logger.info(
        f"ALS Precision@3: {als_precision:.4f}, Recall@3: {als_recall:.4f}, Samples: {als_count}"
    )
    logger.info(
        f"LightFM Precision@3: {lightfm_precision:.4f}, Recall@3: {lightfm_recall:.4f}, Samples: {lightfm_count}"
    )

    # Ждём перед следующим вычислением (1 час)
    await asyncio.sleep(3600)


async def main():
    # Запускаем сервер Prometheus на порту 8002
    start_http_server(8002)
    logger.info("Started Prometheus metrics server on port 8002")
    await calculate_metrics()

if __name__ == "__main__":
    asyncio.run(main())
