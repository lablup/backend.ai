from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.common import ObjectNotFound


class DefinitionFileNotFound(ObjectNotFound):
    object_name = "definition-file"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointNotFound(ObjectNotFound):
    object_name = "endpoint"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DeploymentRevisionNotFound(ObjectNotFound):
    object_name = "deployment-revision"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class UserNotFoundInDeployment(ObjectNotFound):
    object_name = "user in deployment"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DeploymentHasNoTargetRevision(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/deployment-has-no-target-revision"
    error_title = "Deployment has no target revision."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidDeploymentStrategy(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-deployment-strategy"
    error_title = "Unknown or invalid deployment strategy."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidDeploymentStrategySpec(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-deployment-strategy-spec"
    error_title = "Mismatched deployment strategy spec type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ReplicaCountMismatch(BackendAIError):
    error_type = "https://api.backend.ai/probs/replica-count-mismatch"
    error_title = "Active route count does not match target replica count."

    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(f"Expected {expected} replicas, found {actual}")
        self.expected = expected
        self.actual = actual

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class RouteSessionNotFound(BackendAIError):
    error_type = "https://api.backend.ai/probs/route-session-not-found"
    error_title = "No session associated with route."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RouteSessionTerminated(BackendAIError):
    error_type = "https://api.backend.ai/probs/route-session-terminated"
    error_title = "Route session is in terminal state."

    def __init__(self, session_status: str) -> None:
        super().__init__(f"Session status: {session_status}")
        self.session_status = session_status

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class RouteUnhealthy(BackendAIError):
    error_type = "https://api.backend.ai/probs/route-unhealthy"
    error_title = "Route health check failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
