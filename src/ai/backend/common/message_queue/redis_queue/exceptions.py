<<<<<<< HEAD
=======
from typing import override

from aiohttp import web

>>>>>>> d2ebe76c5 (fix(BA-9049): give the error classes of the agent, common, manager and storage packages an HTTP status (#17132))
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class MessageQueueClosedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/message-queue-closed"
    error_title = "Message Queue Closed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MESSAGE_QUEUE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
