# 🎬 UGC service API

**FastAPI API** для обработки пользовательских действий с фильмами: **лайки**, **отзывы**, **закладки** и **просмотры**.

## 🚀 Возможности

- 🔐 Аутентификация через JWT
- ❤️ Лайки и рейтинг фильмов
- 📝 Отзывы с возможностью лайков/дизлайков
- 📌 Закладки фильмов
- 🎥 Учёт просмотренных фильмов

#### 🎞️ Фильмы
- POST `/movies/movie_timestamp/` — Отметить фильм как просмотренный
- GET `/movies/users/{user_id}/movie_timestamps/` — Получить информацию о просмотрах пользователя

#### ❤️ Лайки
- POST `/likes/` — Поставить лайк фильму с оценкой
- GET `/likes/movies/{movie_id}/likes/` — Получить все лайки фильма
- GET `/likes/movies/{movie_id}/average_rating/` — Средняя оценка фильма
- DELETE `/likes/{like_id}/` — Удалить лайк

#### 📝 Отзывы
- POST `/reviews/` — Создать отзыв
- GET `/reviews/movies/{movie_id}/reviews/` — Получить отзывы о фильме
- POST `/reviews/{review_id}/like/` — Лайкнуть отзыв
- POST `/reviews/{review_id}/dislike/` — Дизлайкнуть отзыв
- DELETE `/reviews/{review_id}/` — Удалить отзыв

#### 📌 Закладки
- POST `/bookmarks/` — Добавить фильм в закладки
- GET `/bookmarks/users/{user_id}/bookmarks/` — Получить закладки пользователя
- DELETE `/bookmarks/{bookmark_id}/` — Удалить закладку

#### 🗃️ Структура данных
MongoDB используется в качестве базы данных. 
Все документы содержат поле _id (тип ObjectId). Ссылки на пользователя и фильм хранятся как строки.


### Генератор данных 
docker exec graduate_work-ugc_service-1 python scripts/pg_to_mongo_transfer.py - формирование базы фильмов из постгреса в монго для генерации по ним событий
docker exec graduate_work-ugc_service-1 python scripts/generate_data.py - генерация событий

