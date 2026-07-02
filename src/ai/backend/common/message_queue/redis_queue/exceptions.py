from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class MessageQueueClosedError(BackendAIError):
    error_type = "https://api.backend.ai/probs/message-queue-closed"
    error_title = "Message Queue Closed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MESSAGE_QUEUE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
