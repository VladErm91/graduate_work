# recommendation_service/models/watch_history.py
from sqlalchemy import Column, ForeignKey, DateTime, Interval, Boolean, String
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime, timedelta, timezone
from models.user import User
from models.movie import Movie


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))  # Исправлено на users.user_id
    movie_id = Column(String, ForeignKey("movies.movie_id"))
    watched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    watch_time = Column(Interval, default=timedelta(minutes=10))
    completed = Column(Boolean, default=False)
    user = relationship("User")
    movie = relationship("Movie")

# class WatchHistory(Base):
#     __tablename__ = "watch_history"

#     id = Column(String, primary_key=True, index=True)
#     user_id = Column(String, ForeignKey("users.user_id"))  # Исправлено на users.user_id
#     movie_id = Column(String, ForeignKey("movies.movie_id"))
#     watched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
#     completed = Column(Boolean, default=False)
#     user = relationship("User")
#     movie = relationship("Movie")
