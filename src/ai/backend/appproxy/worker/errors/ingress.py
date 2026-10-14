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


class IngressRevisionConflictError(BackendAIError, web.HTTPConflict):
    """Raised when an upsert carries a revision older than the one held."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/ingress-revision-conflict"
    error_title = "Ingress revision is older than the one held."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.UPSERT,
            error_detail=ErrorDetail.CONFLICT,
        )


class IngressAuthorityMismatchError(BackendAIError, web.HTTPBadRequest):
    """Raised when an ingress belongs to an authority other than the worker's."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/ingress-authority-mismatch"
    error_title = "Ingress belongs to another authority."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.UPSERT,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class IngressStateUnavailableError(BackendAIError, web.HTTPNotImplemented):
    """Raised when the worker has not built its ingress state."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/ingress-state-unavailable"
    error_title = "Ingress state is not available on this worker."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class IngressWriteNotSupportedError(BackendAIError, web.HTTPNotImplemented):
    """Raised when the worker holds no in-memory layer to write to."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/ingress-write-not-supported"
    error_title = "This worker does not accept ingress writes."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.UPSERT,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class IngressNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised for a frontend key remembered missing within negative-ttl."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/ingress-not-found"
    error_title = "No ingress serves this frontend."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
