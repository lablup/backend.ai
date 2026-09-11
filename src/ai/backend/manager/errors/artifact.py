from typing import override

from aiohttp import web

from ai.backend.common.data.entity.artifact import ArtifactEntityType
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionFieldType
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


class ArtifactNotFoundError(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-not-found"
    error_title = "Artifact Not Found"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ArtifactEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class ArtifactRevisionNotVerified(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-not-verified"
    error_title = "Artifact Not Verified"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ArtifactRevisionFieldType(), ActionOperationType.UPDATE, ErrorDetail.BAD_REQUEST
        )


class ArtifactRevisionUpdateError(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/artifact-update-failed"
    error_title = "Artifact Update Failed"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ArtifactRevisionFieldType(), ActionOperationType.UPDATE, ErrorDetail.INTERNAL_ERROR
        )


class ArtifactRevisionDeletionBadRequestError(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-deletion-failed"
    error_title = "Artifact Deletion Bad Request"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ArtifactRevisionFieldType(), ActionOperationType.PURGE, ErrorDetail.BAD_REQUEST
        )


class ArtifactDeletionError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/artifact-deletion-failed"
    error_title = "Artifact Deletion Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactAssociationDeletionError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/artifact-association-deletion-failed"
    error_title = "Artifact Association Deletion Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_ASSOCIATION,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactAssociationNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-association-not-found"
    error_title = "Artifact Association Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_ASSOCIATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactRevisionNotApproved(FieldError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/artifact-not-approved"
    error_title = "Artifact Not Approved"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ArtifactRevisionFieldType(), ActionOperationType.GET, ErrorDetail.FORBIDDEN
        )


class ArtifactReadonly(EntityError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/artifact-readonly"
    error_title = "You cannot upload files to readonly artifact storage"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ArtifactEntityType(), ActionOperationType.UPDATE, ErrorDetail.FORBIDDEN
        )


class ArtifactRevisionNotFoundError(FieldError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-revision-not-found"
    error_title = "Artifact Revision Not Found"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ArtifactRevisionFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ArtifactScanLimitExceededError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-scan-limit-exceeded"
    error_title = "Artifact Scan Limit Exceeded"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ArtifactImportBadRequestError(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-bad-import-request"
    error_title = "Artifact Bad Import Request"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ArtifactEntityType(), ActionOperationType.CREATE, ErrorDetail.BAD_REQUEST
        )


class ArtifactImportDelegationError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-import-delegation-failed"
    error_title = "Artifact Import Delegation Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class RemoteReservoirArtifactImportError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/remote-reservoir-artifact-import-error"
    error_title = "Remote Reservoir Artifact Import Error"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
