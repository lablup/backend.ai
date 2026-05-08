"""
API-related exceptions.
"""

from __future__ import annotations

from aiohttp import web
from pydantic import ValidationError

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    format_pydantic_validation_errors,
)


class UnsupportedOperation(BackendAIError):
    error_type = "https://api.backend.ai/probs/unsupported-operation"
    error_title = "This operation is not supported."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class NotImplementedAPI(BackendAIError, web.HTTPNotImplemented):
    error_type = "https://api.backend.ai/probs/not-implemented"
    error_title = "This API is not implemented."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class InvalidAPIParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class GraphQLError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/graphql-error"
    error_title = "GraphQL-generated error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class RateLimitExceeded(BackendAIError, web.HTTPTooManyRequests):
    error_type = "https://api.backend.ai/probs/rate-limit-exceeded"
    error_title = "You have reached your API query rate limit."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class InvalidGraphQLParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-graphql-params"
    error_title = "Invalid GraphQL parameters."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidGraphQLPydanticInput(InvalidGraphQLParameters):
    """
    Raised when a GraphQL input fails Pydantic validation while being
    converted to its DTO. Carries the same structured error payload as
    :class:`PydanticValidationError` so that GraphQL clients can render
    per-field messages.
    """

    error_type = "https://api.backend.ai/probs/invalid-graphql-pydantic-input"
    error_title = "GraphQL input validation failed."

    @classmethod
    def from_pydantic(
        cls, exc: ValidationError, *, location_prefix: str | None = None
    ) -> InvalidGraphQLPydanticInput:
        summary, structured = format_pydantic_validation_errors(
            exc, location_prefix=location_prefix
        )
        return cls(extra_msg=summary, extra_data={"errors": structured})


class InvalidCursor(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-cursor"
    error_title = "Invalid cursor format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
