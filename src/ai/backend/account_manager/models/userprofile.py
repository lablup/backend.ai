from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai.backend.account_manager.types import UserRole, UserStatus
from ai.backend.account_manager.utils import verify_password

from .base import GUID, Base, PasswordColumn, StrEnumType

__all__: tuple[str, ...] = ("UserProfileRow",)


class UserProfileRow(Base):  # type: ignore[misc]
    __tablename__ = "user_profiles"
    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    user_id: Mapped[UUID] = mapped_column("user_id", GUID, nullable=False)
    username: Mapped[str] = mapped_column(
        "username", sa.String(length=64), index=True, nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column("email", sa.String(length=64), index=True, nullable=False)
    password: Mapped[str] = mapped_column("password", PasswordColumn(), nullable=False)
    need_password_change: Mapped[bool | None] = mapped_column(
        "need_password_change", sa.Boolean, server_default=sa.false()
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        "password_changed_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
    )
    full_name: Mapped[str | None] = mapped_column("full_name", sa.String(length=64))
    description: Mapped[str | None] = mapped_column("description", sa.String(length=500))

    role: Mapped[UserRole] = mapped_column(
        "role",
        StrEnumType(UserRole),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        "status", StrEnumType(UserStatus), server_default=UserStatus.ACTIVE.value, nullable=False
    )
    status_info: Mapped[str | None] = mapped_column("status_info", sa.Unicode(), nullable=True)

    created_at = sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    modified_at = sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    )

    user_row = relationship(
        "UserRow",
        back_populates="user_profile_rows",
        primaryjoin="UserRow.uuid == foreign(UserProfileRow.user_id)",
    )


def compare_to_hashed_password(raw_password: str, hashed_password: str) -> bool:
    """
    Compare a raw string password value to hased password.
    """
    return verify_password(raw_password, hashed_password)
