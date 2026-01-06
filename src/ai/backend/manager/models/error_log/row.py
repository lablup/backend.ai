from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ai.backend.manager.data.error_log.types import ErrorLogData, ErrorLogSeverity
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IDColumn,
)

__all__ = ("ErrorLogRow",)


class ErrorLogRow(Base):
    __tablename__ = "error_logs"

    id = IDColumn("id")
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
    )
    severity = sa.Column(
        "severity",
        sa.Enum("critical", "error", "warning", name="errorlog_severity"),
        index=True,
    )
    source = sa.Column("source", sa.String)
    user = sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True, index=True)
    is_read = sa.Column("is_read", sa.Boolean, default=False, index=True)
    is_cleared = sa.Column("is_cleared", sa.Boolean, default=False, index=True)
    message = sa.Column("message", sa.Text)
    context_lang = sa.Column("context_lang", sa.String)
    context_env = sa.Column("context_env", postgresql.JSONB())
    request_url = sa.Column("request_url", sa.String, nullable=True)
    request_status = sa.Column("request_status", sa.Integer, nullable=True)
    traceback = sa.Column("traceback", sa.Text, nullable=True)

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
            created_at=self.created_at,
            severity=ErrorLogSeverity(self.severity),
            source=self.source,
            user=self.user,
            is_read=self.is_read,
            is_cleared=self.is_cleared,
            message=self.message,
            context_lang=self.context_lang,
            context_env=self.context_env,
            request_url=self.request_url,
            request_status=self.request_status,
            traceback=self.traceback,
        )
