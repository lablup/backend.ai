"""
API-related exceptions.
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


class NotImplementedAPI(BackendAIError, web.HTTPNotImplemented):
    error_type = "https://api.backend.ai/probs/not-implemented"
    error_title = "This API is not implemented."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class InvalidAPIParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class RateLimitExceeded(BackendAIError, web.HTTPTooManyRequests):
    error_type = "https://api.backend.ai/probs/rate-limit-exceeded"
    error_title = "You have reached your API query rate limit."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class InvalidGraphQLParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-graphql-params"
    error_title = "Invalid GraphQL parameters."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidCursor(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-cursor"
    error_title = "Invalid cursor format."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
