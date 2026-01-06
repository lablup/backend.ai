from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class ErrorLogSeverity(enum.StrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ErrorLogData:
    id: uuid.UUID
    created_at: datetime
    severity: ErrorLogSeverity
    source: str
    user: uuid.UUID | None
    is_read: bool
    is_cleared: bool
    message: str
    context_lang: str
    context_env: dict[str, Any]
    request_url: str | None
    request_status: int | None
    traceback: str | None
