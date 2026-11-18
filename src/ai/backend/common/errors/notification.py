from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidNotificationChannelSpec(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-channel-spec"
    error_title = "Invalid Notification Channel Specification."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
