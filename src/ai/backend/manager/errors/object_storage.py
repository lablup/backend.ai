from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ObjectStorageNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/object-storage-not-found"
    error_title = "Object Storage Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
