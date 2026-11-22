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


class PluginLoadError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/dra/plugin-load-failed"
    error_title = "The accelerator plugin cannot be loaded."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UnknownDeviceError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/dra/unknown-device"
    error_title = "The claim names a device this node does not have."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class UnsupportedContainerArgsError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/dra/unsupported-container-args"
    error_title = "The plugin injects something a CDI device cannot express."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )
