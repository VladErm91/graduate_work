# recommendation_service/models/user.py

from sqlalchemy import Column, String, Integer
from core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, index=True)
    age = Column(Integer)


# class User(Base):
#     __tablename__ = "users"

#     id = Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         default=uuid.uuid4,
#         unique=True,
#         nullable=False,
#     )
#     first_name = Column(String(50))
#     last_name = Column(String(50))
