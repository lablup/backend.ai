"""
API-related exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class NotImplementedAPI(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/not-implemented"
    error_title = "This API is not implemented."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class DeprecatedAPI(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/deprecated"
    error_title = "This API is deprecated."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.DEPRECATED,
        )


class InvalidAPIParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class GraphQLError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/graphql-error"
    error_title = "GraphQL-generated error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class RateLimitExceeded(BackendAIError, web.HTTPTooManyRequests):
    error_type = "https://api.backend.ai/probs/rate-limit-exceeded"
    error_title = "You have reached your API query rate limit."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
