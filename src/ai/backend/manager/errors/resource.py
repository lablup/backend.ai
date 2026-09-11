"""
Resource management exceptions (groups, domains, scaling groups, instances).
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetEntityType
from ai.backend.common.data.entity.session_template import SessionTemplateEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode

from .common import ObjectNotFound


class DomainNotFound(EntityError, ObjectNotFound):
    object_name = "domain"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(DomainEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class DomainPurgeInProgress(EntityError, web.HTTPConflict):
    """Raised when a write names a domain a purge is working through."""

    error_type = "https://api.backend.ai/probs/domain-purge-in-progress"
    error_title = "Domain is being purged."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(DomainEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT)


class ProjectPurgeInProgress(EntityError, web.HTTPConflict):
    """Raised when a write names a project a purge is working through."""

    error_type = "https://api.backend.ai/probs/project-purge-in-progress"
    error_title = "Project is being purged."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ProjectEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )


class PersonalProjectMemberAdditionError(EntityError, web.HTTPConflict):
    """Raised when a write would add a member to a personal project."""

    error_type = "https://api.backend.ai/probs/personal-project-member-addition"
    error_title = "Personal project takes no members beyond its owner."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ProjectEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )


class PersonalProjectDeletionError(EntityError, web.HTTPConflict):
    """Raised when a personal project is deleted or purged on its own, apart from
    the user it belongs to."""

    error_type = "https://api.backend.ai/probs/personal-project-deletion"
    error_title = "Personal project is removed with its user, not on its own."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ProjectEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT)


class ProjectHasActiveKernelsError(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/project-has-active-kernels"
    error_title = "Project has active kernels."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ProjectEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT)


class ProjectHasVFoldersMountedError(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/project-has-vfolders-mounted"
    error_title = "Project has vfolders mounted to active kernels."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ProjectEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT)


class ProjectHasActiveEndpointsError(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/project-has-active-endpoints"
    error_title = "Project has active endpoints."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ProjectEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT)


class ResourceGroupNotFound(EntityError, ObjectNotFound):
    object_name = "resource group"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceGroupEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class UnresolvableResourceGroup(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/unresolvable-resource-group"
    error_title = (
        "The agent's resource group could not be resolved "
        "and no default resource group is configured."
    )

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DefaultResourceGroupAlreadyExists(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/default-scaling-group-already-exists"
    error_title = "Another resource group is already the default."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceGroupEntityType(), ActionOperationType.UPDATE, ErrorDetail.INVALID_PARAMETERS
        )


class ResourceGroupSessionTypeNotAllowed(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/resource-group-session-type-not-allowed"
    error_title = "Resource group does not allow this session type."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceGroupEntityType(), ActionOperationType.GET, ErrorDetail.INVALID_PARAMETERS
        )


class ProjectNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/project-not-found"
    error_title = "Project not found."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ProjectEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class PersonalProjectNotFound(ProjectNotFound):
    """The user has no personal project, so nothing can be created under their own name.

    Every user is given one at creation, and existing users were backfilled, so this
    states a broken account rather than a missing option.
    """

    error_title = "Personal project not found."


class SessionTemplateNotFound(EntityError, ObjectNotFound):
    object_name = "session template"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionTemplateEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class AppNotFound(ObjectNotFound):
    """Raised when a session's ``service_ports`` names no such app.

    Stays on :class:`BackendAIError`: an entry in that column is a value, not a row.
    Its ``backendai_read_not-found`` code is load-bearing -- WebUI's app launcher
    branches on that exact string -- so do not move it.
    """

    object_name = "app service"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ResourcePresetNotFound(EntityError, ObjectNotFound):
    object_name = "resource preset"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourcePresetEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class RuntimeVariantNotFound(EntityError, ObjectNotFound):
    object_name = "runtime variant"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            RuntimeVariantEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class RuntimeVariantConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-runtime-variant"
    error_title = "Duplicate Runtime Variant"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            RuntimeVariantEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class RuntimeVariantPresetNotFound(EntityError, ObjectNotFound):
    object_name = "runtime variant preset"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            RuntimeVariantPresetEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class RuntimeVariantPresetConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-runtime-variant-preset"
    error_title = "Duplicate Runtime Variant Preset"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            RuntimeVariantPresetEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class ModelCardNotFound(EntityError, ObjectNotFound):
    object_name = "model card"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ModelCardEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ModelCardConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-model-card"
    error_title = "Duplicate Model Card"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ModelCardEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class InvalidProjectTypeForModelCard(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-project-type-for-model-card"
    error_title = "Project is not a MODEL_STORE type."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ProjectEntityType(), ActionOperationType.GET, ErrorDetail.BAD_REQUEST
        )


class NotAModelVFolder(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/not-a-model-vfolder"
    error_title = "VFolder usage_mode is not MODEL."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderEntityType(), ActionOperationType.GET, ErrorDetail.BAD_REQUEST
        )


class DeploymentRevisionPresetNotFound(EntityError, ObjectNotFound):
    object_name = "deployment revision preset"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentPresetEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class DeploymentRevisionPresetConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-deployment-revision-preset"
    error_title = "Duplicate Deployment Revision Preset"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentPresetEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class DomainHasActiveKernels(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/domain-has-active-kernels"
    error_title = "Domain has active kernels."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(DomainEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT)


class DomainHasUsers(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/domain-has-users"
    error_title = "Domain has associated users."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(DomainEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT)


class DomainHasGroups(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/domain-has-groups"
    error_title = "Domain has associated groups."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(DomainEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT)


class DomainDeletionFailed(EntityError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/domain-deletion-failed"
    error_title = "Failed to delete domain."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DomainEntityType(), ActionOperationType.PURGE, ErrorDetail.INTERNAL_ERROR
        )


class InvalidUserUpdateMode(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-user-update-mode"
    error_title = "Invalid user update mode."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidPresetQuery(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-preset-query"
    error_title = "Invalid resource preset query parameters."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class NoCurrentTaskContext(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/no-current-task-context"
    error_title = "No current asyncio task context available."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class DatabaseConnectionUnavailable(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/database-connection-unavailable"
    error_title = "Database connection is not available."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ConfigurationLoadFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/configuration-load-failed"
    error_title = "Failed to load configuration."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class DataTransformationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/data-transformation-failed"
    error_title = "Failed to transform data."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class DBOperationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/db-operation-failed"
    error_title = "Database operation failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
