from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidAPIParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ModelServiceNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/model-service-not-found"
    error_title = "Model service not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GenericForbidden(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/forbidden"
    error_title = "Forbidden."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class EndpointNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/endpoint-not-found"
    error_title = "Endpoint not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointAutoScalingRuleNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/endpoint-auto-scaling-rule-not-found"
    error_title = "Endpoint auto scaling rule not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT_AUTO_SCALING,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RouteNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/route-not-found"
    error_title = "Route not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROUTE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
