"""Exceptions for leader election module."""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class LeaderElectionError(BackendAIError):
    """Base exception for leader election errors."""

    error_type = "https://api.backend.ai/probs/leader-election-error"
    error_title = "Leader Election Error"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.LEADER_ELECTION,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class AlreadyStartedError(LeaderElectionError):
    """Raised when trying to start an already started election or register tasks after start."""

    error_type = "https://api.backend.ai/probs/leader-already-started"
    error_title = "Leader Election Already Started"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.LEADER_ELECTION,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )
