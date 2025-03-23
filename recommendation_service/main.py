from fastapi import FastAPI
from api.endpoints import recommendations

app = FastAPI(title="Recommendation Service")

app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])
