from typing import override

from aiohttp import web

from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class ObjectStorageNotFoundError(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/object-storage-not-found"
    error_title = "Object Storage Not Found"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ObjectStorageEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ObjectStorageOperationNotSupported(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/object-storage-operation-not-supported"
    error_title = "Object Storage Operation Not Supported"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
