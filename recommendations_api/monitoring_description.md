Настройка мониторинга с использованием Prometheus и Grafana в вашем проекте (`recommendation_service`) позволит собирать, хранить и визуализировать метрики производительности, состояния системы и поведения приложения. Это даст вам возможность отслеживать здоровье сервисов, выявлять узкие места и принимать обоснованные решения для оптимизации. Давайте разберём, что именно вы сможете мониторить, какие данные собирать и как их просматривать в Grafana.

---

### Что можно мониторить?

Prometheus собирает метрики в формате временных рядов, которые ваше приложение экспортирует через HTTP-эндпоинт (обычно `/metrics`). Grafana визуализирует эти данные в виде графиков, дашбордов и алертов. Вот ключевые категории и конкретные метрики, которые вы сможете отслеживать в вашем проекте:

#### 1. Метрики приложения (FastAPI)
- **Время обработки запросов**:
  - Среднее, минимальное, максимальное время выполнения запросов к эндпоинтам (`/recommendations/{user_id}`, `/watched`).
  - Количество запросов в секунду (RPS).
  - Процентили времени ответа (например, 95-й и 99-й процентили).
- **Коды ответов HTTP**:
  - Количество успешных запросов (2xx), ошибок клиента (4xx), серверных ошибок (5xx).
- **Количество активных запросов**:
  - Сколько запросов обрабатывается одновременно.
- **Ошибки валидации**:
  - Частота `InvalidId` или других исключений в `recommend.py`.

#### 2. Метрики моделей машинного обучения
- **Время обучения моделей**:
  - Длительность выполнения `partial_train` (LightFM) и `train` (ALS + LightFM).
  - Разделение по типу обучения (полное vs частичное).
- **Частота обучения**:
  - Количество запусков `partial_train` и `train` за период (например, в час или день).
- **Размер матриц**:
  - Количество пользователей и фильмов в `user_ids` и `movie_ids`.
  - Размер матриц `als_user_item_matrix` и `lightfm_user_item_matrix` (в элементах).
- **Ошибки обучения**:
  - Частота сбоев при сохранении в MinIO или загрузке данных из MongoDB.

#### 3. Метрики базы данных (MongoDB)
- **Время выполнения запросов**:
  - Среднее и максимальное время запросов к `watched_movies`, `likes`, `bookmarks`, `movies`.
- **Количество операций**:
  - Частота чтения (`find`) и записи (`insert_one`, `insert_many`).
- **Размер коллекций**:
  - Количество записей в `watched_movies`, `likes`, `bookmarks`, `movies`.
- **Ошибки подключения**:
  - Частота таймаутов или отказов MongoDB.

#### 4. Метрики MinIO
- **Время доступа к моделям**:
  - Длительность загрузки (`get_object`) и сохранения (`put_object`) моделей.
- **Размер моделей**:
  - Размер файлов `als_model.pkl` и `lightfm_model.pkl` в байтах.
- **Ошибки хранения**:
  - Частота сбоев при работе с MinIO (например, недоступность бакета).

#### 5. Метрики Redis и RQ
- **Размер очереди RQ**:
  - Количество задач в очереди (`train_model`, `update_all_recommendations`).
- **Время выполнения задач**:
  - Длительность обработки задач RQ Worker’ом.
- **Частота задач**:
  - Количество выполненных, ожидающих и проваленных задач.
- **Использование Redis**:
  - Количество ключей, память, используемая Redis (`last_train_time` и др.).

#### 6. Метрики системы (контейнеры Docker)
- **Использование CPU**:
  - Нагрузка на процессор для `fastapi`, `mongo`, `minio`, `redis`, `rq_worker`.
- **Использование памяти**:
  - Объём потребляемой памяти каждым контейнером.
- **Сетевые операции**:
  - Объём входящего и исходящего трафика между сервисами.
- **Состояние контейнеров**:
  - Количество перезапусков, статус (running, stopped).

---

### Какие данные можно просматривать в Grafana?

Grafana позволяет создавать дашборды с графиками, таблицами и алертами на основе данных из Prometheus. Вот примеры данных и визуализаций:

#### 1. Дашборд для FastAPI
- **График RPS**: Количество запросов в секунду к `/recommendations/{user_id}` и `/watched`.
- **График времени ответа**: Среднее и 99-й процентиль времени обработки запросов.
- **Панель ошибок**: Количество 4xx и 5xx ответов с разбивкой по эндпоинтам.
- **Тепловая карта**: Распределение времени ответа по времени суток.

#### 2. Дашборд для моделей
- **График времени обучения**: Длительность `partial_train` (каждые 15 минут) и `train` (ежедневно).
- **Счётчик запусков**: Количество вызовов частичного и полного обучения за день.
- **График размеров**: Рост количества пользователей и фильмов в матрицах.
- **Панель ошибок**: Количество сбоев при сохранении моделей в MinIO.

#### 3. Дашборд для MongoDB
- **График запросов**: Частота и время выполнения запросов к каждой коллекции.
- **Панель роста данных**: Количество записей в `watched_movies` и `movies` с течением времени.
- **Счётчик ошибок**: Частота таймаутов или недоступности MongoDB.

#### 4. Дашборд для инфраструктуры
- **График CPU**: Процент использования CPU каждым контейнером.
- **График памяти**: Потребление памяти в МБ для `fastapi`, `mongo`, `redis`.
- **Сетевой трафик**: Входящий и исходящий трафик между сервисами.
- **Состояние задач RQ**: Длина очереди, количество выполненных и проваленных задач.

#### 5. Алерты
- **Высокое время ответа**: Уведомление, если 99-й процентиль времени ответа превышает 1 секунду.
- **Сбой обучения**: Алерт при ошибке сохранения модели в MinIO.
- **Переполнение очереди RQ**: Уведомление, если длина очереди превышает 10 задач.
- **Недоступность сервиса**: Алерт, если контейнер перезапустился более 3 раз за час.

---

### Как это реализовать?

#### 1. Интеграция Prometheus в проект
- **Установка зависимостей**:
  ```bash
  pip install prometheus-client
  ```
- **Добавление метрик в FastAPI**:
  Обновим `main.py` и `recommend.py` для экспорта метрик:
  ```python
  # recommendation_service/main.py
  from fastapi import FastAPI
  from contextlib import asynccontextmanager
  from api.v1 import recommend
  from core.mongo import get_mongo_db
  from workers.tasks import train_model
  from scheduler import start_scheduler
  from prometheus_client import Counter, Histogram, start_http_server
  import logging

  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)

  # Метрики Prometheus
  REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
  REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'Request Latency', ['endpoint'])

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      db = await get_mongo_db()
      watched_count = await db["watched_movies"].count_documents({})
      if watched_count == 0:
          logger.info("No records found in watched_movies. Skipping model training.")
      else:
          if not (recommendation_model.als_loaded and recommendation_model.lightfm_loaded):
              train_model()
      start_scheduler()
      start_http_server(8001)  # Prometheus метрики на порту 8001
      yield
      logger.info("Application shutting down")

  app = FastAPI(lifespan=lifespan)
  app.include_router(recommend.router, prefix="/api/v1")
  ```

  ```python
  # recommendation_service/api/v1/recommend.py
  from fastapi import APIRouter, Depends, HTTPException
  from motor.motor_asyncio import AsyncIOMotorDatabase
  from core.mongo import get_mongo_db
  from ml.recommendation_model import recommendation_model
  from workers.tasks import train_model
  from bson import ObjectId
  from bson.errors import InvalidId
  from main import REQUEST_COUNT, REQUEST_LATENCY
  from datetime import datetime
  import time

  router = APIRouter()

  @router.get("/recommendations/{user_id}")
  async def get_recommendations(user_id: str, n: int = 3, model_type: str = "als", db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
      start_time = time.time()
      try:
          ObjectId(user_id)
          result = await recommendation_model.get_recommendations(user_id, db, n, model_type)
          REQUEST_COUNT.labels(method='GET', endpoint='/recommendations', status='200').inc()
          REQUEST_LATENCY.labels(endpoint='/recommendations').observe(time.time() - start_time)
          return result
      except InvalidId:
          REQUEST_COUNT.labels(method='GET', endpoint='/recommendations', status='400').inc()
          REQUEST_LATENCY.labels(endpoint='/recommendations').observe(time.time() - start_time)
          raise HTTPException(status_code=400, detail=f"Invalid user_id: '{user_id}'")

  @router.post("/watched")
  async def add_watched_movie(data: dict, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
      start_time = time.time()
      try:
          user_id = ObjectId(data["user_id"])
          movie_id = ObjectId(data["movie_id"])
          watched_entry = {
              "user_id": user_id,
              "movie_id": movie_id,
              "complete": data.get("complete", False),
              "timestamp": datetime.utcnow()
          }
          await db["watched_movies"].insert_one(watched_entry)
          train_model(partial=True, train_als=False)  # Опционально
          REQUEST_COUNT.labels(method='POST', endpoint='/watched', status='200').inc()
          REQUEST_LATENCY.labels(endpoint='/watched').observe(time.time() - start_time)
          return {"status": "added"}
      except (KeyError, InvalidId):
          REQUEST_COUNT.labels(method='POST', endpoint='/watched', status='400').inc()
          REQUEST_LATENCY.labels(endpoint='/watched').observe(time.time() - start_time)
          raise HTTPException(status_code=400, detail="Invalid user_id or movie_id")
  ```
- **Метрики моделей**:
  Добавим в `recommendation_model.py`:
  ```python
  from prometheus_client import Histogram, Counter

  TRAIN_DURATION = Histogram('model_train_duration_seconds', 'Model Training Duration', ['type'])
  TRAIN_COUNT = Counter('model_train_count_total', 'Total Model Trainings', ['type'])

  class RecommendationModel:
      async def partial_train(self, db: AsyncIOMotorDatabase, last_timestamp=None, train_als: bool = False):
          start_time = time.time()
          # ... (логика partial_train) ...
          TRAIN_DURATION.labels(type='partial').observe(time.time() - start_time)
          TRAIN_COUNT.labels(type='partial').inc()

      async def train(self, db: AsyncIOMotorDatabase):
          start_time = time.time()
          # ... (логика train) ...
          TRAIN_DURATION.labels(type='full').observe(time.time() - start_time)
          TRAIN_COUNT.labels(type='full').inc()
  ```

#### 2. Настройка Prometheus
- Добавьте Prometheus в `docker-compose.yml`:
  ```yaml
  version: "3.8"
  services:
    prometheus:
      image: prom/prometheus:latest
      volumes:
        - ./prometheus.yml:/etc/prometheus/prometheus.yml
      ports:
        - "9090:9090"
  ```
- Создайте `prometheus.yml`:
  ```yaml
  global:
    scrape_interval: 15s
  scrape_configs:
    - job_name: 'fastapi'
      static_configs:
        - targets: ['fastapi:8001']
    - job_name: 'mongo'
      static_configs:
        - targets: ['mongo:27017']
  ```

#### 3. Настройка Grafana
- Добавьте Grafana в `docker-compose.yml`:
  ```yaml
  services:
    grafana:
      image: grafana/grafana:latest
      ports:
        - "3000:3000"
      environment:
        - GF_SECURITY_ADMIN_PASSWORD=admin
  ```
- Подключите Prometheus как источник данных в Grafana (URL: `http://prometheus:9090`).
- Создайте дашборды с запросами, например:
  - RPS: `rate(http_requests_total[5m])`
  - Время ответа: `histogram_quantile(0.95, sum(rate(http_request_latency_seconds_bucket[5m])) by (le))`
  - Время обучения: `model_train_duration_seconds`

---

### Итог
С Prometheus и Grafana вы сможете мониторить:
- Производительность API (RPS, latency, ошибки).
- Обучение моделей (время, частота, сбои).
- Состояние базы данных и инфраструктуры (CPU, память, сеть).
- Поведение очередей RQ (длина, время задач).

В Grafana вы получите наглядные графики, дашборды и алерты для всех этих метрик. Если хотите внедрить это, я могу помочь с конкретным кодом или настройкой! Что скажете?