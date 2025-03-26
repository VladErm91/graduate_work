# recommendation_service/models/user.py

from sqlalchemy import Column, String, Integer
from core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, index=True)
    age = Column(Integer)
