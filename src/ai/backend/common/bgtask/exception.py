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
