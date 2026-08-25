from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.error_log.types import (
    ErrorLogContent,
    ErrorLogData,
    ErrorLogMeta,
    ErrorLogSeverity,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = [
    "ErrorLogRow",
]


class ErrorLogRow(CreatedAtMixin, Base):
    __tablename__ = "error_logs"
    # The mixin does not index its column, but every read of this table orders by it
    # and pages, so the index is declared here rather than lost to the move.
    __table_args__ = (sa.Index("ix_error_logs_created_at", "created_at"),)

    id: Mapped[ErrorLogID] = mapped_column(
        "id", GUID(ErrorLogID), primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    # Columns keep the historical nullable=True of the imperative table definition;
    # the annotations stay non-Optional because every writer supplies them.
    severity: Mapped[str] = mapped_column(
        "severity",
        sa.Enum("critical", "error", "warning", name="errorlog_severity"),
        nullable=True,
        index=True,
    )
    source: Mapped[str] = mapped_column("source", sa.String, nullable=True)
    user: Mapped[UserID | None] = mapped_column(
        "user", GUID(UserID), sa.ForeignKey("users.uuid"), nullable=True, index=True
    )
    is_read: Mapped[bool] = mapped_column(
        "is_read", sa.Boolean, default=False, nullable=True, index=True
    )
    is_cleared: Mapped[bool] = mapped_column(
        "is_cleared", sa.Boolean, default=False, nullable=True, index=True
    )
    message: Mapped[str] = mapped_column("message", sa.Text, nullable=True)
    context_lang: Mapped[str] = mapped_column("context_lang", sa.String, nullable=True)
    context_env: Mapped[dict[str, Any]] = mapped_column(
        "context_env", postgresql.JSONB(), nullable=True
    )
    request_url: Mapped[str | None] = mapped_column("request_url", sa.String, nullable=True)
    request_status: Mapped[int | None] = mapped_column("request_status", sa.Integer, nullable=True)
    traceback: Mapped[str | None] = mapped_column("traceback", sa.Text, nullable=True)

    def to_dataclass(self) -> ErrorLogData:
        return ErrorLogData(
            id=ErrorLogID(self.id),
            meta=ErrorLogMeta(
                created_at=self.created_at,
                user=self.user,
                source=self.source,
                is_read=self.is_read,
                is_cleared=self.is_cleared,
                context_lang=self.context_lang,
                context_env=self.context_env,
                request_url=self.request_url,
                request_status=self.request_status,
            ),
            content=ErrorLogContent(
                severity=ErrorLogSeverity(self.severity),
                message=self.message,
                traceback=self.traceback,
            ),
        )
