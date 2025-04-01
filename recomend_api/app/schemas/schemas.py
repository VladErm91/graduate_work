from db.db import Base
from sqlalchemy import ARRAY, Column, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID


class Movies(Base):
    __tablename__ = "movies"

    id = Column(String(255), primary_key=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)
    genres = Column(ARRAY(String), nullable=False)

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}
