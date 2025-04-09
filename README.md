### Рекомендательная система
  
API для рекомендаций фильмов на основе предпочтений пользователей и истории просмотров с использованием моделей машинного обучения (ALS и LightFM).

#### Назначение
Проект предоставляет REST API для получения персонализированных рекомендаций фильмов, основанных на данных о просмотрах, лайках и закладках пользователей. Он включает:
- Генерацию рекомендаций с использованием моделей ALS (Alternating Least Squares) и LightFM.
- Поддержку инкрементального и полного обучения моделей.
- Хранение и мониторинг метрик качества (Precision@3, Recall@3) и производительности (время запросов, обучения).
- Интеграцию с внешними сервисами (например, `url_movies_search` для получения топ-фильмов по жанрам).

#### Основные функции
1. **Эндпоинты API**:
   - `GET /api/recommend/v1/recommendations/genres_top`: Возвращает топ-фильмы по любимым жанрам пользователя.
   - `GET /api/recommend/v1/recommendations/{user_id}`: Возвращает персонализированные рекомендации для пользователя.
   - `POST /api/recommend/v1/feedback/{session_id}`: Принимает обратную связь о рекомендациях (liked/unliked).
2. **Обучение моделей**:
   - Полное обучение на всех данных (`train`).
   - Инкрементальное обучение на новых взаимодействиях (`partial_train`).
3. **Мониторинг**:
   - Метрики HTTP-запросов (количество, задержка).
   - Метрики качества рекомендаций (Precision@3, Recall@3).
   - Метрики обучения (время, размер матрицы).
4. **Генерация тестовых данных**:
   - Создание пользователей, фильмов, просмотров, рекомендаций и отзывов для тестирования.

#### Технологический стек
- **Язык**: Python 3.12
- **Фреймворк**: FastAPI
- **Базы данных**:
  - MongoDB (хранение данных о пользователях, фильмах, взаимодействиях).
  - Redis (кэширование рекомендаций).
- **Хранилище моделей**: MinIO
- **Очереди задач**: RQ (Redis Queue)
- **Модели ML**: Implicit (ALS), LightFM
- **Мониторинг**: Prometheus, Grafana
- **Контейнеризация**: Docker, Docker Compose

---

### Архитектура и взаимодействие сервисов

#### Сервисы (из `docker-compose.yml`)
1. **`recommend`**:
   - **Описание**: Основной сервис FastAPI, предоставляющий REST API.
   - **Порты**: 
     - 8084 (API).
     - 8001 (Prometheus метрики HTTP и моделей).
   - **Зависимости**: Redis, MongoDB, MinIO.
   - **Функции**:
     - Обслуживает эндпоинты `/genres_top`, `/recommendations/{user_id}`, `/feedback/{session_id}`.
     - Инициализирует обучение моделей при старте через `lifespan` в `main.py`.
     - Использует `recommendation_model.py` для генерации рекомендаций.
   - **Метрики**: `http_requests_total`, `http_request_latency_seconds`, `recommendation_duration_seconds`, `popular_recommendations_total`, `model_loaded_status`.

2. **`rq_worker`**:
   - **Описание**: Фоновый обработчик задач RQ для обучения моделей.
   - **Зависимости**: Redis, MinIO.
   - **Функции**:
     - Выполняет задачи `train_model` из `workers/tasks.py`, добавленные через RQ.
     - Обновляет модели в MinIO после обучения.

3. **`rq_scheduler`**:
   - **Описание**: Планировщик задач для периодического обучения.
   - **Зависимости**: Redis, MinIO.
   - **Функции**:
     - Запускает `scheduler.py` для периодического вызова `partial_train` (например, раз в 15 минут).

4. **`metrics`**:
   - **Описание**: Сервис для вычисления метрик качества рекомендаций.
   - **Порт**: 8002 (Prometheus метрики).
   - **Зависимости**: MongoDB.
   - **Функции**:
     - Выполняет `evaluate_metrics.py`, вычисляя Precision@3 и Recall@3 каждые 3600 секунд.
     - Экспортирует метрики: `als_precision_at_3`, `lightfm_recall_at_3`, и т.д.

5. **`minio`**:
   - **Описание**: Хранилище объектов для моделей ML.
   - **Порты**: 9000 (API), 9001 (Console).
   - **Функции**:
     - Хранит файлы `als_model.pkl` и `lightfm_model.pkl`.
     - Используется `recommendation_model.py` для загрузки/сохранения моделей.

6. **`redis`**:
   - **Описание**: Кэш и очередь задач.
   - **Порт**: 6379.
   - **Функции**:
     - Кэширует рекомендации в `recommend.py` (TTL 3600 секунд).
     - Хранит задачи RQ для `rq_worker` и `rq_scheduler`.

7. **`mongodb`**:
   - **Описание**: Основная база данных.
   - **Порт**: 27017.
   - **Коллекции**:
     - `users`: Пользователи (`_id`, `username`).
     - `movies`: Фильмы (`_id`, `title`, `genres`, `rating`, `creation_date`).
     - `watched_movies`: Просмотры (`user_id`, `movie_id`, `complete`, `timestamp`).
     - `likes`: Лайки (`user_id`, `movie_id`, `rating`, `timestamp`).
     - `bookmarks`: Закладки (`user_id`, `movie_id`, `timestamp`).
     - `reviews`: Отзывы (`user_id`, `movie_id`, `content`, `publication_date`,`additional_data`,`likes`,`dislikes`).
     - `favourite_genres`: Любимые жанры (`user_id`, `genres`, `timestamp`).
     - `recommendation_logs`: Логи рекомендаций (`user_id`, `session_id`, `source`, `recommendations`, `timestamp`).
     - `feedback`: Отзывы (`user_id`, `session_id`, `movie_id`, `liked`, `timestamp`).
   - **Функции**: Хранит данные для обучения моделей и вычисления метрик.

8. **`prometheus`**:
   - **Описание**: Сервис мониторинга.
   - **Порт**: 9090.
   - **Функции**:
     - Собирает метрики с `recommend:8001` и `metrics:8002` каждые 15 секунд.
     - Конфигурация: `prometheus.yml`.

9. **`grafana`**:
   - **Описание**: Визуализация метрик.
   - **Порт**: 3000.
   - **Функции**:
     - Отображает дашборды с метриками HTTP, обучения, качества рекомендаций.

#### Взаимодействие сервисов
1. **Старт системы**:
   - `recommend` запускается, проверяет наличие данных в `watched_movies` через MongoDB.
   - Если данные есть и модели не загружены из MinIO, добавляет задачу `train_model` в RQ (Redis).
   - `rq_worker` выполняет задачу, обучает модели и сохраняет их в MinIO.
   - `rq_scheduler` периодически запускает `partial_train` через `scheduler.py`.

2. **Запрос рекомендаций**:
   - Клиент отправляет запрос на `GET /recommendations/{user_id}`.
   - `recommend` проверяет кэш в Redis, если нет — вызывает `recommendation_model.get_recommendations`.
   - `recommendation_model` загружает модели из MinIO (если не загружены) и использует данные из MongoDB для рекомендаций.
   - Результат кэшируется в Redis и записывается в `recommendation_logs`.

3. **Обратная связь**:
   - Клиент отправляет `POST /feedback/{session_id}`.
   - `recommend` сохраняет отзыв в `feedback` (MongoDB).

4. **Мониторинг**:
   - `recommend` экспортирует метрики HTTP и моделей на порт 8001.
   - `metrics` вычисляет Precision@3 и Recall@3 из `recommendation_logs` и `feedback`, экспортирует на 8002.
   - Prometheus собирает метрики с обоих портов.
   - Grafana визуализирует данные через дашборд.

5. **Генерация данных**:
   - `generate_mongo_data.py` заполняет MongoDB тестовыми данными для всех коллекций.

---

### Пример использования

1. **Запуск системы**:
   ```bash
   docker-compose up --build -d
   ```

2. **Генерация данных**:
   ```bash
   docker-compose exec recommend python ml/generate_mongo_data.py
   ```

3. **Получение рекомендаций**:
   ```bash
   curl -H "X-Request-Id: test-id" -H "Authorization: Bearer <your-jwt-token>" http://localhost:8084/api/recommend/v1/recommendations/<user_uuid>
   ```
   - Ответ:
     ```json
     {
       "source": "als",
       "recommendations": ["movie_uuid1", "movie_uuid2", "movie_uuid3"],
       "session_id": "session_uuid"
     }
     ```

4. **Отправка отзыва**:
   ```bash
   curl -X POST -H "X-Request-Id: test-id" -H "Authorization: Bearer <your-jwt-token>" -H "Content-Type: application/json" http://localhost:8084/api/recommend/v1/feedback/<session_uuid> -d '{"movie_id": "movie_uuid1", "liked": true}'
   ```

5. **Проверка топ-фильмов по жанрам**:
   ```bash
   curl -H "X-Request-Id: test-id" -H "Authorization: Bearer <your-jwt-token>" http://localhost:8084/api/recommend/v1/recommendations/genres_top?limit=6
   ```

6. **Мониторинг**:
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000` (дашборд "Recommendation Service Metrics").

---

### Поток данных
```
Клиент → [FastAPI: recommend:8084] → [Redis: кэш] → [MongoDB: данные] → [MinIO: модели]
       ↳ [RQ Worker: обучение] ← [Redis: очередь] ← [RQ Scheduler: расписание]
       ↳ [Prometheus: метрики] ← [recommend:8001, metrics:8002] → [Grafana: дашборд]
```


Авторы: [Владислав Ермолаев](https://github.com/VladErm91), [Алексей Никулин](https://github.com/alexeynickulin-web), [Максим Урываев](https://github.com/max-x-x), [Владимир Васильев](https://github.com/vasilevva)