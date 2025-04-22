from typing import Any, Mapping, Optional, Sequence
from uuid import UUID

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class VFolderServiceException(BackendAIError):
    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.SERVICE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderNotFound(VFolderServiceException, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/vfolder-not-found"
    error_title = "Virtual folder not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VFolderCreationFailure(VFolderServiceException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-creation-failed"
    error_title = "Virtual folder creation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class VFolderAlreadyExists(VFolderServiceException, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-already-exists"
    error_title = "Virtual folder already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class InvalidParameter(VFolderServiceException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-parameter"
    error_title = "Invalid parameter."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.API,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InsufficientPrivilege(VFolderServiceException, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/insufficient-privilege"
    error_title = "Insufficient privilege."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.API,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class Forbidden(InvalidParameter, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/forbidden"
    error_title = "Forbidden operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.API,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ObjectNotFound(VFolderServiceException, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/object-not-found"
    error_title = "Object not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ProjectNotFound(VFolderServiceException, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/project-not-found"
    error_title = "Project not found."

    _project_id: Optional[str | UUID]

    def __init__(self, project_id: Optional[str | UUID]) -> None:
        self._project_id = project_id

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InternalServerError(VFolderServiceException, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Internal server error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.SERVICE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ModelServiceDependencyNotCleared(VFolderServiceException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/model-service-dependency-not-cleared"
    error_title = "Cannot delete model VFolders bound to alive model services."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.DELETE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class TooManyVFoldersFound(VFolderServiceException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/too-many-vfolders"
    error_title = "Too many virtual folders found."

    targets: Sequence[Mapping[str, Any]]

    def __init__(self, targets: Sequence[Mapping[str, Any]]) -> None:
        self.targets = targets

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class VFolderFilterStatusNotAvailable(VFolderServiceException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-not-available"
    error_title = "Virtual folder filter status not available."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class VFolderFilterStatusFailed(VFolderServiceException, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-failed"
    error_title = "Virtual folder filter status failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VIRTUAL_FOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
