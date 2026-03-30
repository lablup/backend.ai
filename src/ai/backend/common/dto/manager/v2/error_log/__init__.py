"""
Error log DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.error_log.request import (
    AppendErrorLogInput,
    ListErrorLogsInput,
    MarkClearedInput,
)
from ai.backend.common.dto.manager.v2.error_log.response import (
    AppendErrorLogPayload,
    ErrorLogNode,
    ListErrorLogsPayload,
    MarkClearedPayload,
)
from ai.backend.common.dto.manager.v2.error_log.types import (
    ErrorLogContextInfo,
    ErrorLogRequestInfo,
)

__all__ = (
    # Types (sub-models)
    "ErrorLogContextInfo",
    "ErrorLogRequestInfo",
    # Input models (request)
    "AppendErrorLogInput",
    "ListErrorLogsInput",
    "MarkClearedInput",
    # Node and Payload models (response)
    "AppendErrorLogPayload",
    "ErrorLogNode",
    "ListErrorLogsPayload",
    "MarkClearedPayload",
)
