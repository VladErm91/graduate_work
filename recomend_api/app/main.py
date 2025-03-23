import logging
from contextlib import asynccontextmanager

from api.v1 import recommend
from core.config import settings
from db.db import create_database
from db.redis import close_redis, init_redis
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi_pagination import add_pagination

# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
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
add_pagination(app)


# Define CORS settings
origins = ["*"]  # Allow requests from any origin

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
app.include_router(recomendations.router, prefix="/api/recommend/v1/", tags=[""])



# Эндпойнт для проверки состояния приложения
@app.get("/health")
async def health_check():
    return {"status": "OK"}
