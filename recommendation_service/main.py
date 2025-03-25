# recommendation_service/main.py

from fastapi import FastAPI
from api.v1 import recommendations, history
from db.database import init_db

app = FastAPI(title="Recommendation Service")


@app.on_event("startup")
async def startup():
    await init_db()


app.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
app.include_router(history.router, prefix="/history", tags=["History"])
