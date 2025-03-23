from sqlalchemy import Column, ForeignKey, UUID, DateTime, Interval, Boolean
from sqlalchemy.orm import relationship
from core.database import Base
import uuid
from datetime import datetime, timedelta


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movies.id"))
    watched_at = Column(DateTime, default=datetime.utcnow)
    watch_time = Column(Interval, default=timedelta(minutes=10))
    completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="watch_history")
    movie = relationship("Movie")
