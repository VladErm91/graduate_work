import uuid

from db.db import Base
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    users = relationship("User", secondary="user_roles", back_populates="roles")

    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<Role {self.name}>"
