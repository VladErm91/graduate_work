import datetime
import uuid

from db.db import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


# Основная модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    login = Column(String(255), unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    last_login = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Добавляем флаги для управления доступом
    is_active = Column(Boolean, default=True)  # Отвечает за активность учетной записи
    is_staff = Column(Boolean, default=False)  # Отвечает за доступ в админку
    is_admin = Column(
        Boolean, default=False
    )  # Отвечает за полный доступ (суперпользователь)

    # Связь many-to-many через таблицу user_roles
    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    def __init__(
        self,
        login: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        last_login: datetime.datetime = None,
        created_at: datetime.datetime = None,
        is_active: bool = True,
        is_staff: bool = False,
        is_admin: bool = False,
    ) -> None:
        self.login = login
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.last_login = last_login or datetime.datetime.now(datetime.timezone.utc)
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)
        self.is_active = is_active
        self.is_staff = is_staff
        self.is_admin = is_admin

    def __repr__(self) -> str:
        return f"<User {self.login}>"


class UserActionHistory(Base):
    __tablename__ = "user_action_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


# модель связывающая пользователя и роль
class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
