from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidContainerRegistryProject(BackendAIError, web.HTTPBadRequest):
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class InvalidContainerRegistryURL(BackendAIError, web.HTTPBadRequest):
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
