from typing import override

from ..exception import BackendAIError, ErrorCode, ErrorDetail, ErrorDomain, ErrorOperation


class InvalidTaskMetadataError(BackendAIError):
    error_type = "https://api.backend.ai/probs/invalid-bgtask-metadata"
    error_title = "Invalid Task Metadata"

    @classmethod
    @override
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class BgtaskInvalidMetadata(BackendAIError):
    error_type = "https://api.backend.ai/probs/bgtask-invalid-metadata"
    error_title = "Background Task has invalid metadata"

    @classmethod
    @override
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
