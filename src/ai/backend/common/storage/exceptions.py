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


class InvalidVolumeStatusCheckConfigError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/invalid-volume-status-check-config"
    error_title = "Invalid Volume Status Check Config"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class VolumeMarkerInvalidError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/volume-marker-invalid"
    error_title = "Volume Marker Invalid"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFS_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
