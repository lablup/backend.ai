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


class HammerspaceError(BackendAIError):
    """Base error for Hammerspace-related errors."""


class AuthenticationError(HammerspaceError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/hammerspace-authentication-failure"
    error_title = "Hammerspace API authentication failed."

    @classmethod
    @override
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class ShareNotFound(HammerspaceError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/hammerspace-share-not-found"
    error_title = "Hammerspace has no such share."

    @classmethod
    @override
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
