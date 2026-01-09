from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ai.backend.manager.data.error_log.types import (
    ErrorLogContent,
    ErrorLogData,
    ErrorLogMeta,
    ErrorLogSeverity,
)

from .base import GUID, Base, IDColumn, mapper_registry

__all__ = [
    "error_logs",
    "ErrorLogRow",
]

error_logs = sa.Table(
    "error_logs",
    mapper_registry.metadata,
    IDColumn(),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    sa.Column(
        "severity", sa.Enum("critical", "error", "warning", name="errorlog_severity"), index=True
    ),
    sa.Column("source", sa.String),
    sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True, index=True),
    sa.Column("is_read", sa.Boolean, default=False, index=True),
    sa.Column("is_cleared", sa.Boolean, default=False, index=True),
    sa.Column("message", sa.Text),
    sa.Column("context_lang", sa.String),
    sa.Column("context_env", postgresql.JSONB()),
    sa.Column("request_url", sa.String, nullable=True),
    sa.Column("request_status", sa.Integer, nullable=True),
    sa.Column("traceback", sa.Text, nullable=True),
)


class ErrorLogRow(Base):
    __table__ = error_logs

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
