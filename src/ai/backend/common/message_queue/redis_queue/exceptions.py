from ...exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class MessageQueueClosedError(BackendAIError):
    error_type = "https://api.backend.ai/probs/message-queue-closed"
    error_title = "Message Queue Closed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MESSAGE_QUEUE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
