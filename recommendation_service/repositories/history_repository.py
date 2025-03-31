from sqlalchemy.ext.asyncio import AsyncSession
from models.watch_history import WatchHistory
import uuid
from datetime import datetime, timezone, timedelta


class HistoryRepository:
    @staticmethod
    async def save_user_history(user_id: str, movie_id: str, db: AsyncSession):
        history = WatchHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            movie_id=movie_id,
            watched_at=datetime.now(timezone.utc),
            watch_time=timedelta(minutes=10),
            completed=False,
        )
        db.add(history)
        await db.commit()
