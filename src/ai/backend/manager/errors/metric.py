"""
Metric domain exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidContainerMetricName(BackendAIError, web.HTTPBadRequest):
    """Raised when a container metric name holds a character outside letters, digits, `_`, `:`
    and `-`."""

    error_type = "https://api.backend.ai/probs/invalid-container-metric-name"
    error_title = "Invalid container metric name."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.METRIC,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
