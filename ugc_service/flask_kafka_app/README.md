Локальный запуск flask-kafka-app:

```
gunicorn --workers 4 --worker-class gevent --bind 0.0.0.0:8000 "app:create_app()"
```

Документация API: 
http://localhost:8000/apidocs/

Запуск генератора событий:
```


```

Запуск тестов:
```
docker exec -it ugc_sprint_1-flask-kafka-web-1 pytest


