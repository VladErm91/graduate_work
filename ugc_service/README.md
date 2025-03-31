## Генерация данных для работы с API:

cd mongo_app/app
docker exec ugc_service python scripts/pg_to_mongo_transfer.py - формирование базы фильмов из постгреса в монго для генерации по ним событий
docker exec ugc_service python scripts/generate_data.py - генерация событий и пользователей
```
