"""
Common DTOs for error log management used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AppendErrorLogRequest,
    ListErrorLogsRequest,
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
    # Response DTOs - Data
    "ErrorLogDTO",
    # Response DTOs - Responses
    "AppendErrorLogResponse",
    "ListErrorLogsResponse",
    "MarkClearedResponse",
)
