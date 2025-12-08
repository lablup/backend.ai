"""
Storage and virtual folder-related exceptions.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

from .common import ObjectNotFound

if TYPE_CHECKING:
    from ai.backend.manager.api.vfolder import VFolderRow


class TooManyVFoldersFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-vfolders"
    error_title = "Multiple vfolders found for the operation for a single vfolder."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.CONFLICT,
        )

    def __init__(self, matched_rows: Sequence[VFolderRow]) -> None:
        serialized_matches = [
            {
                "id": row["id"],
                "host": row["host"],
                "user": row["user_email"],
                "user_id": row["user"],
                "group": row["group_name"],
                "group_id": row["group"],
            }
            for row in matched_rows
        ]
        super().__init__(extra_data={"matches": serialized_matches})


class VFolderNotFound(ObjectNotFound):
    object_name = "virtual folder"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class QuotaScopeNotFoundError(ObjectNotFound):
    object_name = "quota scope"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelCardParseError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/model-card-parse-error"
    error_title = "Model Card Parse Error"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_CARD,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class VFolderAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-already-exists"
    error_title = "The virtual folder already exists with the same name."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class VFolderGone(BackendAIError, web.HTTPGone):
    error_type = "https://api.backend.ai/probs/vfolder-gone"
    error_title = "The virtual folder is gone."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.GONE,
        )


class VFolderBadRequest(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-operation-failed"
    error_title = "Virtual folder operation has failed due to bad request."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class VFolderOperationFailed(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-operation-failed"
    error_title = "Virtual folder operation has failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderFilterStatusFailed(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-failed"
    error_title = "Virtual folder status filtering has failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class VFolderFilterStatusNotAvailable(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-not-available"
    error_title = "There is no available virtual folder to filter its status."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderPermissionError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-permission-error"
    error_title = "The virtual folder does not permit the specified permission."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class VFolderInvitationNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/vfolder-invitation-not-found"
    error_title = "Virtual folder invitation not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER_INVITATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VFolderCreationFailure(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-creation-failed"
    error_title = "Virtual folder creation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderGrantAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-grant-already-exists"
    error_title = "Virtual folder grant already exists."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.GRANT,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class VFolderDeletionNotAllowed(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-deletion-not-allowed"
    error_title = "Virtual folder deletion is not allowed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class InsufficientStoragePermission(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage-permission-not-allowed"
    error_title = "The specified storage permission is not allowed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class VFolderInvalidParameter(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-invalid-parameter"
    error_title = "Invalid parameter for virtual folder operation."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class DotfileCreationFailed(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Dotfile creation has failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class DotfileAlreadyExists(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Dotfile already exists."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class DotfileNotFound(ObjectNotFound):
    object_name = "dotfile"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DotfileVFolderPathConflict(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/dotfile-vfolder-path-conflict"
    error_title = "The dotfile path conflicts with a virtual folder path."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class StorageProxyNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage-proxy-not-found"
    error_title = "Storage proxy not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class StorageProxyConnectionError(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/storage-proxy-connection-error"
    error_title = "Failed to connect to storage proxy."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class StorageProxyTimeoutError(BackendAIError, web.HTTPGatewayTimeout):
    error_type = "https://api.backend.ai/probs/storage-proxy-timeout"
    error_title = "Request to storage proxy timed out."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.TIMEOUT,
        )


class UnexpectedStorageProxyResponseError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unexpected-storage-proxy-response"
    error_title = "Unexpected response from storage proxy."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class UnsupportedStorageTypeError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/unsupported-storage-type"
    error_title = "Unsupported storage type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
