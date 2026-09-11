"""
Compute-backend (instance lifecycle) exceptions for the agent.
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


class InstanceNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when an instance referenced by a handle no longer exists."""

    error_type = "https://api.backend.ai/probs/agent/instance-not-found"
    error_title = "Instance not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.INSTANCE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InstanceAlreadyExistsError(BackendAIError, web.HTTPConflict):
    """Raised when creating an instance whose id is already tracked by the backend."""

    error_type = "https://api.backend.ai/probs/agent/instance-already-exists"
    error_title = "Instance already exists."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.INSTANCE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ContainerEnumerationIncomplete(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when the backend could not describe every container it listed.

    A caller diffs its own bookkeeping against this listing, so a short one reads as "these are
    gone" and gets kernels destroyed and ports re-issued. Not answering is the safe failure.
    """

    error_type = "https://api.backend.ai/probs/agent/container-enumeration-incomplete"
    error_title = "Could not enumerate every container."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
