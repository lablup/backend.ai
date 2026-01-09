"""
Service endpoint and model service-related exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

from .common import ObjectNotFound


class NoUpdatesToApply(BackendAIError):
    """Raised when there are no updates to apply to an endpoint."""

    def __init__(self, message: str = "No updates to apply") -> None:
        super().__init__(message)

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointNotFound(ObjectNotFound):
    object_name = "endpoint"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelDefinitionNotFound(ObjectNotFound):
    object_name = "model_definition"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ScalingImpossible(BackendAIError, web.HTTPBadRequest):
    error_title = (
        "Scaling operation cannot be performed due to insufficient resources or constraints."
    )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class AutoScalingRuleNotFound(ObjectNotFound):
    object_name = "auto_scaling_rule"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AutoScalingPolicyNotFound(ObjectNotFound):
    object_name = "auto_scaling_policy"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DeploymentPolicyNotFound(ObjectNotFound):
    object_name = "deployment_policy"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RoutingNotFound(ObjectNotFound):
    object_name = "routing"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROUTE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointTokenNotFound(ObjectNotFound):
    object_name = "endpoint_token"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelServiceNotFound(ObjectNotFound):
    object_name = "model service"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RouteNotFound(ObjectNotFound):
    object_name = "route"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROUTE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelServiceDependencyNotCleared(BackendAIError, web.HTTPBadRequest):
    error_title = "Cannot delete model VFolders bound to alive model services."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class AppServiceStartFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/app-service-start-failed"
    error_title = "Failed to start the application service."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
