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


class VFolderNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/vfolder-not-found"
    error_title = "Virtual folder not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VFolderInvitationNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/vfolder-invitation-not-found"
    error_title = "Virtual folder invitation not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER_INVITATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VFolderCreationFailure(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-creation-failed"
    error_title = "Virtual folder creation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-already-exists"
    error_title = "Virtual folder already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class VFolderGrantAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-already-exists"
    error_title = "Virtual folder already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.GRANT,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class VFolderInvalidParameter(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-parameter"
    error_title = "Invalid parameter."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InsufficientPrivilege(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/insufficient-privilege"
    error_title = "Insufficient privilege."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class Forbidden(VFolderInvalidParameter, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/forbidden"
    error_title = "Forbidden operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ProjectNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/project-not-found"
    error_title = "Project not found."

    _project_id: Optional[str | UUID]

    def __init__(self, project_id: Optional[str | UUID]) -> None:
        self._project_id = project_id

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InternalServerError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Internal server error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ModelServiceDependencyNotCleared(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/model-service-dependency-not-cleared"
    error_title = "Cannot delete model VFolders bound to alive model services."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class TooManyVFoldersFound(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/too-many-vfolders"
    error_title = "Too many virtual folders found."

    targets: Sequence[Mapping[str, Any]]

    def __init__(self, targets: Sequence[Mapping[str, Any]]) -> None:
        self.targets = targets

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.CONFLICT,
        )


class VFolderFilterStatusNotAvailable(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-not-available"
    error_title = "Virtual folder filter status not available."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class VFolderFilterStatusFailed(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-failed"
    error_title = "Virtual folder filter status failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
