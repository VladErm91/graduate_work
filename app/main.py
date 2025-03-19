import logging
from contextlib import asynccontextmanager

# from api.v1 import 
from core.config import settings
from db.db import create_database
from db.redis import close_redis, init_redis
from fastapi import FastAPI, HTTPException, Request, status
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
    docs_url="/api/auth/openapi",
    openapi_url="/api/auth/openapi.json",
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
async def requests_limit_checker(request: Request, call_next):
    try:
        await request_limiter(request)
    except HTTPException:
        return ORJSONResponse(
            content={"message": "Слишком много запросов от данного пользователя"}
        )
    response = await call_next(request)
    return response


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


if settings.enable_tracing:
    configure_tracer()
    # FastAPIInstrumentor.instrument_app(app)


app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.include_router(auth.router, prefix="/api//v1/", tags=[""])



# Эндпойнт для проверки состояния приложения
@app.get("/health")
async def health_check():
    return {"status": "OK"}
