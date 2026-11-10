from typing import override

from aiohttp import web

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyFieldType
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionFieldType
from ai.backend.common.data.entity.keypair import KeyPairFieldType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderUUID
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
from ai.backend.manager.errors.common import ObjectNotFound


class DeploymentDefinitionFileReadError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/deployment-definition-file-read-error"
    error_title = "Failed to read deployment definition file."

    def __init__(
        self,
        *,
        vfolder_id: VFolderUUID,
        filename: str,
        cause: Exception,
    ) -> None:
        super().__init__(f"File '{filename}' in vfolder {vfolder_id}: {cause}")

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_DEPLOYMENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class EndpointNotFound(EntityError, ObjectNotFound):
    object_name = "endpoint"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class DeploymentRevisionNotFound(FieldError, ObjectNotFound):
    object_name = "deployment-revision"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            DeploymentRevisionFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class UserNotFoundInDeployment(EntityError, ObjectNotFound):
    object_name = "user in deployment"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(UserEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class NoActiveKeypairForDeployment(FieldError, ObjectNotFound):
    object_name = "active keypair for deployment user"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(KeyPairFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class DeploymentHasNoTargetRevision(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/deployment-has-no-target-revision"
    error_title = "Deployment has no target revision."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            DeploymentRevisionFieldType(),
            ActionOperationType.GET,
            ErrorDetail.INVALID_PARAMETERS,
        )


class RevisionMissingModelVFolder(FieldError, web.HTTPBadRequest):
    """A revision's model vfolder reference is null.

    Raised when the draft / session pipeline reads a
    ``ModelRevisionData`` whose ``model_mount_config.vfolder_id`` has
    collapsed to ``NULL`` because the backing vfolder row was deleted
    (``vfolders.id`` SET NULL FK on ``deployment_revisions.model``).
    The revision is preserved for history, but no new session can be
    spawned from it until a new revision pointing at a live model
    vfolder takes over.
    """

    error_type = "https://api.backend.ai/probs/revision-missing-model-vfolder"
    error_title = "Deployment revision has no model vfolder."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            DeploymentRevisionFieldType(),
            ActionOperationType.GET,
            ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidDeploymentStrategy(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-deployment-strategy"
    error_title = "Unknown or invalid deployment strategy."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            DeploymentPolicyFieldType(),
            ActionOperationType.GET,
            ErrorDetail.INVALID_PARAMETERS,
        )


class RouteSessionNotFound(EntityError):
    error_type = "https://api.backend.ai/probs/route-session-not-found"
    error_title = "No session associated with route."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(SessionEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class RouteSessionTerminated(EntityError):
    error_type = "https://api.backend.ai/probs/route-session-terminated"
    error_title = "Route session is in terminal state."

    def __init__(self, session_status: str) -> None:
        super().__init__(f"Session status: {session_status}")
        self.session_status = session_status

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionEntityType(), ActionOperationType.GET, ErrorDetail.INVALID_PARAMETERS
        )


class IncompleteRevisionData(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/incomplete-revision-data"
    error_title = "Revision data is missing required fields."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            DeploymentRevisionFieldType(),
            ActionOperationType.GET,
            ErrorDetail.INVALID_PARAMETERS,
        )
