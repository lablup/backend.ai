"""
Storage and virtual folder-related exceptions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, override

from aiohttp import web

from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.entity.vfolder_invitation import VFolderInvitationEntityType
from ai.backend.common.data.entity.vfolder_permission import VFolderPermissionFieldType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode

from .common import ObjectNotFound


class TooManyVFoldersFound(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/too-many-vfolders"
    error_title = "Multiple vfolders found for the operation for a single vfolder."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(VFolderEntityType(), ActionOperationType.GET, ErrorDetail.CONFLICT)

    def __init__(self, matched_rows: Sequence[Mapping[str, Any]]) -> None:
        serialized_matches = [
            {
                "id": row.get("id") if isinstance(row, Mapping) else row.id,
                "host": row.get("host") if isinstance(row, Mapping) else row.host,
                "user": row.get("user_email") if isinstance(row, Mapping) else row.user_email,
                "user_id": row.get("user") if isinstance(row, Mapping) else row.user,
                "group": row.get("group_name") if isinstance(row, Mapping) else row.group_name,
                "group_id": row.get("group") if isinstance(row, Mapping) else row.group,
            }
            for row in matched_rows
        ]
        super().__init__(extra_data={"matches": serialized_matches})


class VFolderOwnerNotFound(EntityError, web.HTTPInternalServerError):
    """The scope a vfolder was to be created in does not exist.

    A personal folder names its project by its owner, so this states that the owner has
    no personal project — every user is given one, making it a broken account.
    """

    error_type = "https://api.backend.ai/probs/vfolder-owner-not-found"
    error_title = "The vfolder has no owning project."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderEntityType(), ActionOperationType.CREATE, ErrorDetail.NOT_FOUND
        )


class VFolderNotFound(EntityError, ObjectNotFound):
    object_name = "virtual folder"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(VFolderEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class QuotaScopeNotFoundError(ObjectNotFound):
    object_name = "quota scope"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelCardParseError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/model-card-parse-error"
    error_title = "Model Card Parse Error"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_CARD,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class VFolderAlreadyExists(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-already-exists"
    error_title = "The virtual folder already exists with the same name."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderEntityType(), ActionOperationType.CREATE, ErrorDetail.ALREADY_EXISTS
        )


class VFolderGone(EntityError, web.HTTPGone):
    error_type = "https://api.backend.ai/probs/vfolder-gone"
    error_title = "The virtual folder is gone."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(VFolderEntityType(), ActionOperationType.GET, ErrorDetail.GONE)


class VFolderBadRequest(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-bad-request"
    error_title = "Virtual folder operation has failed due to bad request."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class VFolderOperationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/vfolder-operation-failed"
    error_title = "Virtual folder operation has failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderFilterStatusFailed(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-failed"
    error_title = "Virtual folder status filtering has failed."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderEntityType(), ActionOperationType.GET, ErrorDetail.BAD_REQUEST
        )


class VFolderFilterStatusNotAvailable(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-not-available"
    error_title = "There is no available virtual folder to filter its status."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderPermissionError(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/vfolder-permission-error"
    error_title = "The virtual folder does not permit the specified permission."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class VFolderInvitationNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/vfolder-invitation-not-found"
    error_title = "Virtual folder invitation not found."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderInvitationEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class VFolderCreationFailure(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/vfolder-creation-failed"
    error_title = "Virtual folder creation failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderGrantAlreadyExists(FieldError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/vfolder-grant-already-exists"
    error_title = "Virtual folder grant already exists."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            VFolderPermissionFieldType(), ActionOperationType.CREATE, ErrorDetail.ALREADY_EXISTS
        )


class VFolderDeletionNotAllowed(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-deletion-not-allowed"
    error_title = "Virtual folder deletion is not allowed."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderEntityType(), ActionOperationType.DELETE, ErrorDetail.BAD_REQUEST
        )


class VFolderHasLinkedModelCard(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-has-linked-model-card"
    error_title = "Virtual folder has linked model card(s)."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderEntityType(), ActionOperationType.PURGE, ErrorDetail.BAD_REQUEST
        )


class InsufficientStoragePermission(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/storage-permission-not-allowed"
    error_title = "The specified storage permission is not allowed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class VFolderInvalidParameter(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-invalid-parameter"
    error_title = "Invalid parameter for virtual folder operation."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class DotfileCreationFailed(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/dotfile-creation-failed"
    error_title = "Dotfile creation has failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class DotfileAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/dotfile-already-exists"
    error_title = "Dotfile already exists."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class DotfileNotFound(ObjectNotFound):
    object_name = "dotfile"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DotfileVFolderPathConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/dotfile-vfolder-path-conflict"
    error_title = "The dotfile path conflicts with a virtual folder path."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class StorageProxyNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage-proxy-not-found"
    error_title = "Storage proxy not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class StorageProxyConnectionError(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/storage-proxy-connection-error"
    error_title = "Failed to connect to storage proxy."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class StorageProxyTimeoutError(BackendAIError, web.HTTPGatewayTimeout):
    error_type = "https://api.backend.ai/probs/storage-proxy-timeout"
    error_title = "Request to storage proxy timed out."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.TIMEOUT,
        )


class UnexpectedStorageProxyResponseError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unexpected-storage-proxy-response"
    error_title = "Unexpected response from storage proxy."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UnsupportedStorageTypeError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/unsupported-storage-type"
    error_title = "Unsupported storage type."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
