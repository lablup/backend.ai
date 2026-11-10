from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = (
    "EventPayloadDecodingError",
    "EventPayloadEncodingError",
)


class EventPayloadEncodingError(BackendAIError):
    """
    Raised when an event cannot be rendered as the JSON body it is published as.

    This means a field type is not JSON-representable, which is a defect in the event
    definition rather than anything about the message that carries it.
    """

    error_type = "https://api.backend.ai/probs/event-payload-encoding-failed"
    error_title = "Event Payload Encoding Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.EVENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class EventPayloadDecodingError(BackendAIError):
    """
    Raised when a message body does not validate against the event it names.

    Redelivering the same body cannot change the outcome, so a consumer treats this as
    permanent rather than retriable.
    """

    error_type = "https://api.backend.ai/probs/event-payload-decoding-failed"
    error_title = "Event Payload Decoding Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.EVENT,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
