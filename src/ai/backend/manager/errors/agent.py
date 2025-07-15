"""
Agent-related exceptions.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

from .common import ObjectNotFound


class AgentNotFound(ObjectNotFound):
    object_name = "agent"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
