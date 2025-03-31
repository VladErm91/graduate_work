import logging
from contextlib import asynccontextmanager

from api.v1 import genres, recommend
from core.config import settings
from db.db import create_database
from db.redis import close_redis, init_redis
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware

# Логгирование
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных
    logging.info("Initializing the database...")
    await create_database()

    print("Database created successfully.")
    # Инициализация Redis
    logging.info("Initializing Redis...")
    await init_redis()

    # Yield управление в FastAPI
    yield

    # Закрытие соединения с Redis при завершении
    logging.info("Closing Redis...")
    await close_redis()


app = FastAPI(
    title=settings.project_name,
    docs_url="/api/recommend/openapi",
    openapi_url="/api/recommend/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.middleware("http")
async def before_request(request: Request, call_next):

    response = await call_next(request)
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "X-Request-Id is required"},
        )
    return response


app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.include_router(
    recommend.router, prefix="/api/recommend/v1/recomm", tags=["recommend"]
)
app.include_router(genres.router, prefix="/api/recommend/v1/favorites", tags=["genres"])


# Эндпойнт для проверки состояния приложения
@app.get("/health")
async def health_check():
    return {"status": "OK"}
