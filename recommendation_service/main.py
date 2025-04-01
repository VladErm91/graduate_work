# recommendation_service/main.py

from fastapi import FastAPI
from api.v1 import recommendations  # , history
from core.database import init_db
from contextlib import asynccontextmanager


app = FastAPI(title="Recommendation Service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app.lifespan_context = lifespan

app.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
# app.include_router(history.router, prefix="/history", tags=["History"])
# app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
