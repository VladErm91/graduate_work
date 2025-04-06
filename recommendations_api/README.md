Проект на данный момент представляет собой сложную систему рекомендаций, полностью переведённую на MongoDB, с поддержкой двух моделей (ALS и LightFM), асинхронным обучением через RQ, A/B-тестированием и сбором метрик. 

---

### Компоненты проекта

#### 1. **FastAPI (основной сервис)**
- **Файл**: `main.py`, `api/v1/genres.py`
- **Функция**: веб-сервер, предоставляющий API для выбора и обработки любимых жанров пользователя.
- **Основные эндпоинты**:
  - `POST /genres`: Добавляет список любимых жанров пользователя не более 3х для дальнейшего их использования в построении рекомендаций.
- **Файл**: `main.py`, `api/v1/recommendations.py`
- **Функция**: Основной веб-сервер, предоставляющий API для получения рекомендаций и обратной связи.
- **Основные эндпоинты**:
 - `GET /genres_top`: Возвращает список наиболее популярных фильмов на основе любимых жанров пользователя. без использвания моделей.
 - `GET /recommendations/{user_id}`: Возвращает рекомендации для пользователя (ALS или LightFM, случайно или по параметру `model`).
 - `POST /feedback/{session_id}`: Принимает обратную связь (лайк/дизлайк) по рекомендациям.
- **Взаимодействие**:
  - Обращается к `recommendation_model.py` для генерации рекомендаций.
  - Использует Redis для кэширования результатов.
  - Сохраняет рекомендации и фидбек в MongoDB (`recommendation_logs`, `feedback`).



#### 2. **Recommendation Model**
- **Файл**: `recommendation_model.py`
- **Функция**: Логика обучения и генерации рекомендаций.
- **Компоненты**:
  - **ALS**: Коллаборативная фильтрация из `implicit`.
  - **LightFM**: Гибридная модель (коллаборативная + контентная) из `lightfm`, использует `genres` из `movies`.
- **Хранение**: Модели сохраняются в MinIO (`als_model.pkl`, `lightfm_model.pkl`).
- **Взаимодействие**:
  - Получает данные из MongoDB (`watched_movies`, `likes`, `bookmarks`) для обучения.
  - Генерирует рекомендации по запросу от FastAPI.
  - Возвращает результат с `session_id` для отслеживания.

#### 3. **MongoDB**
- **Функция**: Основное хранилище данных.
- **Коллекции**:
  - `users`: Информация о пользователях.
  - `movies`: Данные о фильмах (включая `genres`, `rating`).
  - `watched_movies`: История просмотров (вес 1.0 для завершённых, 0.5 для незавершённых).
  - `likes`: Оценки фильмов (вес = `rating / 10`).
  - `bookmarks`: Закладки (вес 0.3).
  - `recommendation_logs`: Логи рекомендаций (с `session_id`, `model_type`).
  - `feedback`: Обратная связь от пользователей (с `session_id`, `liked`).
- **Взаимодействие**:
  - Используется FastAPI, `recommendation_model.py` и `tasks.py` через `motor`.

#### 4. **Redis**
- **Функция**: Кэширование рекомендаций и управление очередями RQ.
- **Ключи**:
  - `recommendations:{user_id}:{model_type}`: Кэш рекомендаций для каждого пользователя и модели.
- **Взаимодействие**:
  - FastAPI проверяет/записывает кэш.
  - RQ использует Redis для хранения задач.

#### 5. **RQ (Redis Queue)**
- **Файл**: `tasks.py`
- **Функция**: Асинхронное выполнение задач (обучение моделей, обновление рекомендаций).
- **Задачи**:
  - `train_model`: Обучение ALS и LightFM.
  - `update_all_recommendations`: Обновление кэша рекомендаций для всех пользователей.
  - `update_recommendations`: Обновление кэша для одного пользователя.
- **Взаимодействие**:
  - Ставит задачи в очередь через Redis.
  - Выполняется `rq_worker`.

#### 6. **RQ Scheduler**
- **Файл**: `scheduler.py`
- **Функция**: Планирование задач по расписанию.
- **Расписание**:
  - 00:00: `train_model` — обучение моделей.
  - 00:30: `update_all_recommendations` — обновление кэша рекомендаций.
- **Взаимодействие**:
  - Использует Redis для управления задачами.
  - Запускает задачи через RQ.

#### 7. **MinIO**
- **Функция**: Хранение обученных моделей.
- **Объекты**:
  - `als_model.pkl`: Модель ALS.
  - `lightfm_model.pkl`: Модель LightFM.
- **Взаимодействие**:
  - `recommendation_model.py` сохраняет и загружает модели.

#### 8. **Kafka**
- **Функция**: Потоковая обработка событий (например, обновление данных).
- **Взаимодействие**:
  - Пока не активно используется для обучения/рекомендаций, но может быть интегрирован для обработки новых взаимодействий в реальном времени.

#### 9. **Metrics**
- **Файл**: `evaluate_metrics.py`
- **Функция**: Вычисление метрик Precision@K и Recall@K на основе `recommendation_logs` и `feedback`.
- **Взаимодействие**:
  - Читает данные из MongoDB.
  - Логирует результаты для анализа.

#### 10. **Генератор данных**
- **Файл**: `generate_mongo_data.py`
- **Функция**: Генерация тестовых данных для MongoDB.
- **Взаимодействие**:
  - Заполняет коллекции `users`, `movies`, `watched_movies`, `likes`, `bookmarks`.

---

### Как всё работает вместе

1. **Запуск системы**:
   - `docker-compose up` запускает все сервисы: FastAPI, MongoDB, Redis, RQ Worker, RQ Scheduler, MinIO, Kafka.
   - `generate_mongo_data.py` заполняет MongoDB тестовыми данными (если нужно).

2. **Обучение моделей**:
   - `scheduler.py` в 00:00 ставит задачу `train_model` в очередь RQ.
   - RQ Worker выполняет `train_model`, который:
     - Читает данные из MongoDB (`watched_movies`, `likes`, `bookmarks`).
     - Обучает ALS и LightFM в `recommendation_model.py`.
     - Сохраняет модели в MinIO.

3. **Обновление рекомендаций**:
   - `scheduler.py` в 00:30 ставит задачу `update_all_recommendations`.
   - RQ Worker:
     - Получает список пользователей из MongoDB.
     - Для каждого пользователя вызывает `update_recommendations` (ALS и LightFM).
     - Кэширует результаты в Redis.

4. **Запрос рекомендаций**:
   - Пользователь запрашивает `GET /recommendations/{user_id}`.
   - FastAPI:
     - Проверяет кэш в Redis.
     - Если кэша нет, вызывает `recommendation_model.get_recommendations`.
     - Сохраняет результат в Redis и `recommendation_logs` (MongoDB).
     - Возвращает рекомендации с `session_id`.

5. **Обратная связь**:
   - Пользователь отправляет `POST /feedback/{session_id}` с `movie_id` и `liked`.
   - FastAPI сохраняет фидбек в MongoDB (`feedback`).

6. **Анализ метрик**:
   - `evaluate_metrics.py` читает `recommendation_logs` и `feedback` из MongoDB.
   - Вычисляет Precision@3 и Recall@3 для ALS и LightFM.
   - Логирует результаты.

---

### Схема работы (ASCII-арт)

```
+-------------------+       +-------------------+       +-------------------+
|     FastAPI       |<----->|      Redis        |<----->|       RQ Worker   |
| - GET /recs       |       | - Cache recs      |       | - Train models    |
| - POST /feedback  |       | - Queue tasks     |       | - Update recs     |
+-------------------+       +-------------------+       +-------------------+
          |                        ^                           ^
          v                        |                           |
+-------------------+       +-------------------+       +-------------------+
|     MongoDB       |<----->| Recommendation   |<----->|     RQ Scheduler  |
| - Users, Movies   |       | Model (ALS, LFM) |       | - 00:00 Train     |
| - Watched, Likes  |       | - Train, Recs    |       | - 00:30 Update    |
| - Logs, Feedback  |       +-------------------+       +-------------------+
          |                        |
          v                        v
+-------------------+       +-------------------+
|     MinIO         |       |     Metrics       |
| - ALS/LFM models  |       | - Precision@K     |
+-------------------+       | - Recall@K        |
                            +-------------------+
```

**Описание схемы**:
- **FastAPI** — точка входа, взаимодействует с Redis (кэш), MongoDB (данные) и `Recommendation Model` (логика).
- **Redis** — посредник для кэша и очередей RQ.
- **RQ Worker** — выполняет задачи из очереди (обучение, обновление).
- **RQ Scheduler** — планирует задачи в Redis.
- **MongoDB** — хранит все данные.
- **MinIO** — хранит модели.
- **Metrics** — анализирует результаты.

---

### Взаимодействие шаг за шагом
1. **Старт**:
   - RQ Scheduler ставит задачи в очередь через Redis.
   - RQ Worker начинает выполнение.

2. **Обучение** (00:00):
   - `train_model` → MongoDB (данные) → `Recommendation Model` (обучение) → MinIO (сохранение).

3. **Обновление** (00:30):
   - `update_all_recommendations` → MongoDB (список пользователей) → `Recommendation Model` (рекомендации) → Redis (кэш).

4. **Запрос**:
   - FastAPI → Redis (проверка кэша) → `Recommendation Model` (если кэша нет) → MongoDB (логи) → Клиент.

5. **Фидбек**:
   - FastAPI → MongoDB (`feedback`).

6. **Метрики**:
   - `evaluate_metrics.py` → MongoDB → Логи.

---

### Итог
Проект состоит из FastAPI (API), `Recommendation Model` (логика), MongoDB (данные), Redis (кэш/очереди), RQ (асинхронность), MinIO (хранение моделей), RQ Scheduler (расписание) и Metrics (анализ). Всё работает в связке, обеспечивая асинхронное обучение, рекомендации и A/B-тестирование.

```bash
docker-compose exec fastapi python scripts/generate_mongo_data.py
docker-compose exec fastapi python -c "from workers.tasks import train_model; train_model()"
docker-compose exec fastapi python ml/evaluate_metrics.py
```

docker exec graduate_work-recommend-1 python -c "from workers.tasks import update_all_recommendations; update_all_recommendations()"