"""
Common DTOs for error log management used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AppendErrorLogRequest,
    ListErrorLogsRequest,
    MarkClearedPathParam,
)
from .response import (
    AppendErrorLogResponse,
    ErrorLogDTO,
    ListErrorLogsResponse,
    MarkClearedResponse,
)

__all__ = (
    # Request DTOs
    "AppendErrorLogRequest",
    "ListErrorLogsRequest",
    "MarkClearedPathParam",
    # Response DTOs - Data
    "ErrorLogDTO",
    # Response DTOs - Responses
    "AppendErrorLogResponse",
    "ListErrorLogsResponse",
    "MarkClearedResponse",
)
