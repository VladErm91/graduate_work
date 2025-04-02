
import uuid

from sqlalchemy import Column, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from db.db import Base

class Movies(Base):
    __tablename__ = "movies"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    genres = Column(ARRAY(String), nullable=False)

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}
