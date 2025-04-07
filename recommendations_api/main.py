import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware

from api.v1 import genres, recommend
from core.config import db, settings
from ml.recommendation_model import recommendation_model
from workers.tasks import train_model

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Проверяем наличие записей в watched_movies
    watched_count = await db["watched_movies"].count_documents({})
    if watched_count == 0:
        logger.info("No records found in watched_movies. Skipping model training.")
    else:
        # Проверяем статус моделей и запускаем обучение, если они отсутствуют
        if not (
            recommendation_model.als_loaded and recommendation_model.lightfm_loaded
        ):
            logger.info(
                "One or both models are missing and data exists. Enqueuing training task..."
            )
            train_model()  # Запускаем обучение в фоновом режиме через RQ
    yield

    logger.info("Application shutting down")


app = FastAPI(
    title=settings.project_name,
    docs_url="/api/recommend/openapi",
    openapi_url="/api/recommend/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    description="API for movie recommendations based on user preferences and viewing history.",
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
    recommend.router, prefix="/api/recommend/v1/recommendations", tags=["recommend"]
)
app.include_router(genres.router, prefix="/api/recommend/v1/favorites", tags=["genres"])


# Эндпойнт для проверки состояния приложения
@app.get("/health")
async def health_check():
    return {"status": "OK"}
