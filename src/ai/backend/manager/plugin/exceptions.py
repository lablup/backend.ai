"""
This module defines a series of Backend.AI's plugin-specific errors.
"""

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class PluginError(web.HTTPBadRequest, BackendAIError):
    error_type = "https://api.backend.ai/probs/plugin-error"
    error_title = "Plugin generated error"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SERVICE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class PluginConfigurationError(PluginError):
    error_type = "https://api.backend.ai/probs/plugin-config-error"
    error_title = "Plugin configuration error"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SERVICE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
