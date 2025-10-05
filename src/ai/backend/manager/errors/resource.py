"""
Resource management exceptions (groups, domains, scaling groups, instances).
"""

from __future__ import annotations

from typing import Any, Optional, Union

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

from .common import ObjectNotFound


class DomainNotFound(ObjectNotFound):
    object_name = "domain"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GroupNotFound(ObjectNotFound):
    object_name = "user group (or project)"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GroupHasActiveKernelsError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/group-has-active-kernels"
    error_title = "Group has active kernels."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class GroupHasVFoldersMountedError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/group-has-vfolders-mounted"
    error_title = "Group has vfolders mounted to active kernels."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class GroupHasActiveEndpointsError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/group-has-active-endpoints"
    error_title = "Group has active endpoints."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class ScalingGroupNotFound(ObjectNotFound):
    object_name = "scaling group"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ScalingGroupDeletionFailure(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/scaling-group-deletion-failure"
    error_title = "Failed to delete scaling group."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class InstanceNotFound(ObjectNotFound):
    object_name = "agent instance"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.INSTANCE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InstanceNotAvailable(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/instance-not-available"
    error_title = "There is no available instance."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.INSTANCE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ProjectNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/project-not-found"
    error_title = "Project not found."

    def __init__(self, project_id: Optional[Union[str, Any]] = None) -> None:
        self._project_id = project_id

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class TaskTemplateNotFound(ObjectNotFound):
    object_name = "task template"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.TEMPLATE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AppNotFound(ObjectNotFound):
    object_name = "app service"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DomainDataProcessingError(BackendAIError, web.HTTPInternalServerError):
    """
    Error that occurs when processing domain data fails.
    This includes failures in converting database rows to domain data objects.
    """

    error_type = "https://api.backend.ai/probs/domain-data-processing-error"
    error_title = "Failed to process domain data."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ScalingGroupProxyTargetNotFound(ObjectNotFound):
    object_name = "scaling group proxy target"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ResourcePresetNotFound(ObjectNotFound):
    object_name = "resource preset"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AgentNotFound(ObjectNotFound):
    object_name = "agent"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DomainCreationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/domain-creation-failed"
    error_title = "Failed to create domain."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class DomainNodeCreationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/domain-node-creation-failed"
    error_title = "Failed to create domain node."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class DomainHasActiveKernels(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/domain-has-active-kernels"
    error_title = "Domain has active kernels."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class DomainHasUsers(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/domain-has-users"
    error_title = "Domain has associated users."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class DomainHasGroups(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/domain-has-groups"
    error_title = "Domain has associated groups."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class DomainUpdateNotAllowed(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/domain-update-not-allowed"
    error_title = "Domain update not allowed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidDomainConfiguration(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-domain-configuration"
    error_title = "Invalid domain configuration."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AllocationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/allocation-failed"
    error_title = "Failed to allocate resources."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class InvalidUserUpdateMode(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-user-update-mode"
    error_title = "Invalid user update mode."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidPresetQuery(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-preset-query"
    error_title = "Invalid resource preset query parameters."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
