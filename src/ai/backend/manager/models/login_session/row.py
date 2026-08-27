from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.common.data.entity.login_history import LoginHistoryID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.auth.login_session_types import (
    LoginAttemptResult,
    LoginSessionStatus,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IPAddressColumn,
    StrEnumType,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

if TYPE_CHECKING:
    from ai.backend.manager.data.auth.login_session_types import LoginHistoryData, LoginSessionData

__all__ = ("LoginSessionRow", "LoginHistoryRow")


class LoginSessionRow(CreatedAtMixin, Base):
    __tablename__ = "login_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    session_token: Mapped[str] = mapped_column(
        "session_token", sa.String(64), unique=True, nullable=False, index=True
    )
    user_id: Mapped[UserID] = mapped_column(
        "user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_key: Mapped[str] = mapped_column("access_key", sa.String(20), nullable=False)
    login_client_type_id: Mapped[LoginClientTypeID | None] = mapped_column(
        "login_client_type_id",
        GUID(LoginClientTypeID),
        sa.ForeignKey("login_client_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[LoginSessionStatus] = mapped_column(
        "status",
        StrEnumType(LoginSessionStatus),
        nullable=False,
        default=LoginSessionStatus.ACTIVE,
        server_default=LoginSessionStatus.ACTIVE.value,
        index=True,
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        "last_accessed_at", sa.DateTime(timezone=True), nullable=True
    )
    invalidated_at: Mapped[datetime | None] = mapped_column(
        "invalidated_at", sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (sa.Index("ix_login_sessions_user_id_status", "user_id", "status"),)

    def to_data(self) -> LoginSessionData:
        from ai.backend.manager.data.auth.login_session_types import (
            LoginSessionData as _LoginSessionData,
        )

        return _LoginSessionData(
            id=self.id,
            session_token=self.session_token,
            user_id=self.user_id,
            access_key=self.access_key,
            status=self.status,
            created_at=self.created_at,
            last_accessed_at=self.last_accessed_at,
            invalidated_at=self.invalidated_at,
        )


class LoginHistoryRow(Base):
    __tablename__ = "login_history"

    id: Mapped[LoginHistoryID] = mapped_column(
        "id", GUID(LoginHistoryID), primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    user_id: Mapped[UserID] = mapped_column(
        "user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    domain_name: Mapped[str] = mapped_column("domain_name", sa.String(64), nullable=False)
    result: Mapped[LoginAttemptResult] = mapped_column(
        "result",
        StrEnumType(LoginAttemptResult),
        nullable=False,
        index=True,
    )
    fail_reason: Mapped[str | None] = mapped_column("fail_reason", sa.Text, nullable=True)
    # The address of the request that produced this record, not of the session it closes:
    # an eviction or an admin revocation carries the address of whoever triggered it.
    client_ip: Mapped[str | None] = mapped_column("client_ip", IPAddressColumn, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (sa.Index("ix_login_history_user_id_created_at", "user_id", "created_at"),)

    def to_data(self) -> LoginHistoryData:
        from ai.backend.manager.data.auth.login_session_types import (
            LoginHistoryData as _LoginHistoryData,
        )

        return _LoginHistoryData(
            id=self.id,
            user_id=self.user_id,
            domain_name=self.domain_name,
            result=self.result,
            fail_reason=self.fail_reason,
            client_ip=self.client_ip,
            created_at=self.created_at,
        )
