from abc import abstractmethod
from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class OpenIDRedirectError(BackendAIError):
    """An authorization failure sent back to the webui as the ``bai_error`` query value."""

    @abstractmethod
    def error_slug(self) -> str:
        raise NotImplementedError


class InvalidSession(OpenIDRedirectError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/invalid-openid-session"
    error_title = "The OpenID session is invalid or has expired."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )

    @override
    def error_slug(self) -> str:
        return "invalid-openid-session"


class OpenIDAuthenticationFailed(OpenIDRedirectError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/openid-not-authenticated"
    error_title = "Not authenticated by OpenID Provider"

    def __init__(self) -> None:
        # Legacy reason phrase, kept for clients that already read it.
        super().__init__(reason=self.error_title)

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )

    @override
    def error_slug(self) -> str:
        return "openid-not-authenticated"


class OpenIDAccessDenied(OpenIDRedirectError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/openid-access-denied"
    error_title = "The OpenID provider denied the sign-in."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )

    @override
    def error_slug(self) -> str:
        return "openid-access-denied"


class OpenIDGroupNotAllowed(OpenIDRedirectError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/openid-group-not-allowed"
    error_title = "The user does not belong to a group allowed to access this resource."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )

    @override
    def error_slug(self) -> str:
        return "openid-group-not-allowed"


class OpenIDDomainNotFound(OpenIDRedirectError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/openid-domain-not-found"
    error_title = "The domain in the OpenID group mapping does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.NOT_FOUND,
        )

    @override
    def error_slug(self) -> str:
        return "openid-domain-not-found"


class OpenIDProviderMisconfigured(OpenIDRedirectError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/openid-provider-misconfigured"
    error_title = "The OpenID provider rejected the client configuration."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    @override
    def error_slug(self) -> str:
        return "openid-provider-misconfigured"


class OpenIDProviderUnavailable(OpenIDRedirectError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/openid-provider-unavailable"
    error_title = "The OpenID provider is unavailable."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    @override
    def error_slug(self) -> str:
        return "openid-provider-unavailable"


class OpenIDEndpointNotConfigured(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/openid-endpoint-not-configured"
    error_title = "Neither well_known nor the OpenID endpoint is configured."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_READY,
        )
