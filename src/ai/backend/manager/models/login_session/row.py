from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.login_session.types import LoginSessionExpiryReason
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

__all__: Sequence[str] = ("LoginSessionRow",)


class LoginSessionRow(Base):  # type: ignore[misc]
    __tablename__ = "login_sessions"
    __table_args__ = (
        sa.UniqueConstraint("session_token", name="uq_login_sessions_session_token"),
        sa.Index("ix_login_sessions_user_uuid", "user_uuid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    user_uuid: Mapped[uuid.UUID] = mapped_column(
        "user_uuid",
        GUID,
        sa.ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    session_token: Mapped[str] = mapped_column(
        "session_token",
        sa.String(length=512),
        nullable=False,
    )
    client_ip: Mapped[str] = mapped_column(
        "client_ip",
        sa.String(length=64),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    expired_at: Mapped[datetime | None] = mapped_column(
        "expired_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )
    reason: Mapped[LoginSessionExpiryReason | None] = mapped_column(
        "reason",
        StrEnumType(LoginSessionExpiryReason),
        nullable=True,
    )
