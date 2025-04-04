from fastapi import FastAPI
from api.v1 import recommendations  # , history, metrics
from core.database import init_db
from contextlib import asynccontextmanager
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Функция жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Инициализация базы данных...")
    await init_db()
    logger.info("✅ База данных инициализирована!")
    yield
    logger.info("🛑 Остановка сервиса...")


# Инициализация FastAPI
app = FastAPI(title="Recommendation Service", lifespan=lifespan)

# Список всех роутеров
ROUTERS = [
    (recommendations.router, "/recommendations", ["Recommendations"]),
    # (history.router, "/history", ["History"]),
    # (metrics.router, "/metrics", ["Metrics"]),
]

# Автоматическая регистрация роутеров
for router, prefix, tags in ROUTERS:
    app.include_router(router, prefix=prefix, tags=tags)

logger.info("🚀 Recommendation Service запущен!")
