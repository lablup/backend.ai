"""JWT authentication exceptions for GraphQL Federation."""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class JWTError(BackendAIError):
    """
    Base exception for JWT-related errors in GraphQL Federation authentication.

    All JWT-specific exceptions inherit from this base class.
    """

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class JWTExpiredError(JWTError, web.HTTPUnauthorized):
    """
    JWT token has expired.

    Raised when attempting to use a token past its expiration time.
    """

    error_type = "https://api.backend.ai/probs/jwt-expired"
    error_title = "JWT token has expired."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.DATA_EXPIRED,
        )


class JWTInvalidSignatureError(JWTError, web.HTTPUnauthorized):
    """
    JWT signature verification failed.

    Raised when the token's signature doesn't match the expected signature,
    indicating the token may have been tampered with or was signed with
    a different secret key.
    """

    error_type = "https://api.backend.ai/probs/jwt-invalid-signature"
    error_title = "JWT signature verification failed."


class JWTInvalidClaimsError(JWTError, web.HTTPUnauthorized):
    """
    JWT claims are missing or invalid.

    Raised when required claims are missing from the token or when
    claim values don't meet validation requirements (e.g., invalid role,
    wrong issuer).
    """

    error_type = "https://api.backend.ai/probs/jwt-invalid-claims"
    error_title = "JWT claims are invalid."


class JWTDecodeError(JWTError, web.HTTPUnauthorized):
    """
    Failed to decode JWT token.

    Raised when the token cannot be decoded, typically due to malformed
    token structure or encoding issues.
    """

    error_type = "https://api.backend.ai/probs/jwt-decode-error"
    error_title = "Failed to decode JWT token."
