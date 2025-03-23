import uuid

from db.db import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID


def create_partition(target, connection, **kw) -> None:
    """creating partition by user_sign_in"""
    connection.execute(
        text(
            """CREATE TABLE IF NOT EXISTS "users_auth_in_smart" PARTITION OF "history_auth" FOR VALUES IN ('smart')"""
        )
    )
    connection.execute(
        text(
            """CREATE TABLE IF NOT EXISTS "users_auth_in_mobile" PARTITION OF "history_auth" FOR VALUES IN ('mobile')"""
        )
    )
    connection.execute(
        text(
            """CREATE TABLE IF NOT EXISTS "users_auth_in_web" PARTITION OF "history_auth" FOR VALUES IN ('web')"""
        )
    )


class AuthenticationHistory(Base):
    __tablename__ = "history_auth"

    __table_args__ = (
        UniqueConstraint("id", "user_device_type"),
        {
            "postgresql_partition_by": "LIST (user_device_type)",
            "listeners": [("after_create", create_partition)],
        },
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        # unique=True,
        nullable=False,
        index=True,
    )

    success = Column(
        Boolean,
        nullable=False,
        comment="Идентификатор, был ли вход успешным",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания записи",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Дата обновления записи",
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment=" id входящего пользователя",
    )

    user_device_type = Column(Text, primary_key=True)

    def __repr__(self):
        return f"<UserSignIn {self.user_id}:{self.created_at}>"
