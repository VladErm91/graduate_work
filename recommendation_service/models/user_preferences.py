# recommendation_service/models/user_preferences.py
from sqlalchemy import Column, String, ForeignKey
from core.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    algorithm = Column(String, default="A")  # "A" или "B"
