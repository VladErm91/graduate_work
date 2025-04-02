## Генерация данных для работы с API:

cd mongo_app/app
docker exec graduate_work-ugc_service-1 python scripts/pg_to_mongo_transfer.py - формирование базы фильмов из постгреса в монго для генерации по ним событий

docker exec graduate_work-ugc_service-1 python scripts/pg_mongo_users.py - генерация пользователей
docker exec graduate_work-ugc_service-1 python scripts/generate_data.py - генерация событий
```
