# recommendation_service/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Метрики для HTTP-запросов
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_latency_seconds',
    'Request Latency',
    ['endpoint']
)

# Метрики для обучения моделей (если используются в recommendation_model.py)
TRAIN_DURATION = Histogram(
    'model_train_duration_seconds',
    'Model Training Duration',
    ['type']
)
TRAIN_COUNT = Counter(
    'model_train_count_total',
    'Total Model Trainings',
    ['type']
)
MATRIX_SIZE = Gauge(
    'matrix_size_elements',
    'Number of Elements in User-Item Matrix',
    ['model']
)

# Метрики для качества моделей (если используются в evaluate_metrics.py)
ALS_PRECISION = Gauge('als_precision_at_3', 'Precision@3 for ALS model')
ALS_RECALL = Gauge('als_recall_at_3', 'Recall@3 for ALS model')
ALS_SAMPLES = Gauge('als_samples', 'Number of ALS samples evaluated')
LIGHTFM_PRECISION = Gauge('lightfm_precision_at_3', 'Precision@3 for LightFM model')
LIGHTFM_RECALL = Gauge('lightfm_recall_at_3', 'Recall@3 for LightFM model')
LIGHTFM_SAMPLES = Gauge('lightfm_samples', 'Number of LightFM samples evaluated')