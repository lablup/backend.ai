"""
Common and generic exceptions that don't belong to a specific domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.plugin.hook import HookResult

if TYPE_CHECKING:
    pass


class URLNotFound(BackendAIError, web.HTTPNotFound):  # TODO: Misused now.
    error_type = "https://api.backend.ai/probs/url-not-found"
    error_title = "Unknown URL path."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ObjectNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/object-not-found"
    object_name = "object"

    def __init__(
        self,
        extra_msg: Optional[str] = None,
        extra_data: Optional[Any] = None,
        *,
        object_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        if object_name:
            self.object_name = object_name
        self.error_title = f"No such {self.object_name}."
        super().__init__(extra_msg, extra_data, **kwargs)

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GenericBadRequest(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Bad request."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class GenericForbidden(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Forbidden operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class RejectedByHook(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/rejected-by-hook"
    error_title = "Operation rejected by a hook plugin."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.HOOK,
            error_detail=ErrorDetail.FORBIDDEN,
        )

    @classmethod
    def from_hook_result(cls, result: HookResult) -> RejectedByHook:
        return cls(
            extra_msg=result.reason,
            extra_data={
                "plugins": result.src_plugin,
            },
        )


class MethodNotAllowed(BackendAIError, web.HTTPMethodNotAllowed):
    error_type = "https://api.backend.ai/probs/method-not-allowed"
    error_title = "HTTP Method Not Allowed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InternalServerError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Internal server error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ServerMisconfiguredError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/server-misconfigured"
    error_title = "Service misconfigured."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ServiceUnavailable(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/service-unavailable"
    error_title = "Serivce unavailable."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ServerFrozen(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/server-frozen"
    error_title = "The server is frozen due to maintenance. Please try again later."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class Forbidden(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/forbidden"
    error_title = "Forbidden operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )
