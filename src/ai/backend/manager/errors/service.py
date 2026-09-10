"""
Service endpoint and model service-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleFieldType
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyFieldType
from ai.backend.common.data.entity.deployment_token import DeploymentTokenFieldType
from ai.backend.common.data.entity.replica import ReplicaFieldType
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
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode

from .common import GenericForbidden, ObjectNotFound


class NoUpdatesToApply(BackendAIError):
    """Raised when there are no updates to apply to an endpoint."""

    def __init__(self, message: str = "No updates to apply") -> None:
        super().__init__(message)

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointNotFound(EntityError, ObjectNotFound):
    object_name = "endpoint"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ModelDefinitionNotFound(ObjectNotFound):
    object_name = "model_definition"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ScalingImpossible(EntityError, web.HTTPBadRequest):
    error_title = (
        "Scaling operation cannot be performed due to insufficient resources or constraints."
    )

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )


class AutoScalingRuleNotFound(FieldError, ObjectNotFound):
    object_name = "auto_scaling_rule"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            AutoScalingRuleFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class AutoScalingPolicyNotFound(ObjectNotFound):
    object_name = "auto_scaling_policy"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DeploymentPolicyNotFound(FieldError, ObjectNotFound):
    object_name = "deployment_policy"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            DeploymentPolicyFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class RoutingNotFound(FieldError, ObjectNotFound):
    object_name = "routing"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(ReplicaFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class EndpointTokenNotFound(FieldError, ObjectNotFound):
    object_name = "endpoint_token"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            DeploymentTokenFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ModelServiceNotFound(EntityError, ObjectNotFound):
    object_name = "model service"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class RouteNotFound(FieldError, ObjectNotFound):
    object_name = "route"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(ReplicaFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class ModelServiceDependencyNotCleared(EntityError, web.HTTPBadRequest):
    error_title = "Cannot delete model VFolders bound to alive model services."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            VFolderEntityType(), ActionOperationType.DELETE, ErrorDetail.CONFLICT
        )


class AppServiceStartFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/app-service-start-failed"
    error_title = "Failed to start the application service."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class EndpointAccessForbiddenError(EntityError, GenericForbidden):
    """Raised when user does not have permission to access an endpoint."""

    error_title = "Access to this endpoint is forbidden."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentEntityType(), ActionOperationType.GET, ErrorDetail.FORBIDDEN
        )


class EndpointAutoScalingRuleNotFound(FieldError, ObjectNotFound):
    object_name = "endpoint auto scaling rule"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            AutoScalingRuleFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )
