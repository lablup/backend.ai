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

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ObjectStorageOperationNotSupported(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/object-storage-operation-not-supported"
    error_title = "Object Storage Operation Not Supported"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
