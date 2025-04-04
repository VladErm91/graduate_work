import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware

from api.v1 import genres, recommend
from core.config import settings

# Логгирование
logging.basicConfig(level=logging.INFO)


app = FastAPI(
    title=settings.project_name,
    docs_url="/api/recommend/openapi",
    openapi_url="/api/recommend/openapi.json",
    default_response_class=ORJSONResponse,
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
