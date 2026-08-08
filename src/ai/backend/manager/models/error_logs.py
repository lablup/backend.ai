from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.error_log.types import (
    ErrorLogContent,
    ErrorLogData,
    ErrorLogMeta,
    ErrorLogSeverity,
)

from .base import GUID, Base

__all__ = [
    "ErrorLogRow",
]


class ErrorLogRow(Base):
    __tablename__ = "error_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
        nullable=False,
    )
    # Columns keep the historical nullable=True of the imperative table definition;
    # the annotations stay non-Optional because __init__ always assigns them.
    severity: Mapped[str] = mapped_column(
        "severity",
        sa.Enum("critical", "error", "warning", name="errorlog_severity"),
        nullable=True,
        index=True,
    )
    source: Mapped[str] = mapped_column("source", sa.String, nullable=True)
    user: Mapped[uuid.UUID | None] = mapped_column(
        "user", GUID, sa.ForeignKey("users.uuid"), nullable=True, index=True
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

    def __init__(
        self,
        severity: ErrorLogSeverity,
        source: str,
        message: str,
        context_lang: str,
        context_env: dict[str, Any],
        user: uuid.UUID | None = None,
        is_read: bool = False,
        is_cleared: bool = False,
        request_url: str | None = None,
        request_status: int | None = None,
        traceback: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.severity = severity.value
        self.source = source
        self.user = user
        self.is_read = is_read
        self.is_cleared = is_cleared
        self.message = message
        self.context_lang = context_lang
        self.context_env = context_env
        self.request_url = request_url
        self.request_status = request_status
        self.traceback = traceback
        if created_at:
            self.created_at = created_at

    def to_dataclass(self) -> ErrorLogData:
        return ErrorLogData(
            id=self.id,
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
