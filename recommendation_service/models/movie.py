from sqlalchemy import Column, String, Integer, Float
from core.database import Base


class Movie(Base):
    __tablename__ = "movies"

    movie_id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    genres = Column(String)
    directors = Column(String)
    rating = Column(Float)
