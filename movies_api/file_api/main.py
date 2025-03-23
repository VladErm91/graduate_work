from contextlib import asynccontextmanager

from api.v1 import file_endpoint
from core.config import settings
from db.minio import close_minio_conn, create_bucket, start_minio_client
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_minio_client()
    await create_bucket(settings.bucket_name)

    yield
    await close_minio_conn()

app = FastAPI(
    title=settings.project_name,
    docs_url="/api/files/openapi",
    openapi_url="/api/files/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(file_endpoint.router, prefix="/api/v1/files", tags=["files"])
