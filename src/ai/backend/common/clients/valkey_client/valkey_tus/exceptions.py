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


class TusLeaseHeldError(BackendAIError, web.HTTPConflict):
    """Another storage-proxy instance holds the per-session TUS write lease."""

    error_type = "https://api.backend.ai/probs/storage/tus-lease-held"
    error_title = "TUS session lease is held by another storage-proxy"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class TusLeaseLostError(BackendAIError, web.HTTPConflict):
    """Per-session TUS write lease expired and was reclaimed by another holder mid-write."""

    error_type = "https://api.backend.ai/probs/storage/tus-lease-lost"
    error_title = "TUS session lease lost mid-write"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class TusSessionNotFoundError(BackendAIError, web.HTTPNotFound):
    """No offset entry exists for this TUS session (never registered or TTL elapsed)."""

    error_type = "https://api.backend.ai/probs/storage/tus-session-not-found"
    error_title = "TUS upload session not found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
