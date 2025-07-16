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


class EndpointNotFound(ObjectNotFound):
    object_name = "endpoint"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RoutingNotFound(ObjectNotFound):
    object_name = "routing"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROUTE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointTokenNotFound(ObjectNotFound):
    object_name = "endpoint_token"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelServiceNotFound(ObjectNotFound):
    object_name = "model service"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RouteNotFound(ObjectNotFound):
    object_name = "route"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROUTE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelServiceDependencyNotCleared(BackendAIError, web.HTTPBadRequest):
    error_title = "Cannot delete model VFolders bound to alive model services."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )
