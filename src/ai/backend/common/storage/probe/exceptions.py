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


class InvalidStorageStatusObservation(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-storage-status-observation"
    error_title = "The storage status observation is not one the check would record."

    @classmethod
    @override
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
