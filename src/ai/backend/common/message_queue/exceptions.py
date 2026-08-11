from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidMessagePayloadError(BackendAIError):
    """
    Raised when a received message does not conform to the message envelope contract.
    """

    error_type = "https://api.backend.ai/probs/invalid-message-payload"
    error_title = "Invalid Message Payload"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MESSAGE_QUEUE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
