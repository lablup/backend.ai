from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class VASTError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/vast/generic"
    error_title = "VAST Error"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VASTAPIError(VASTError):
    error_type = "https://api.backend.ai/probs/storage/vast/api-error"
    error_title = "VAST API Error"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class VASTUnauthorizedError(VASTAPIError):
    error_type = "https://api.backend.ai/probs/storage/vast/unauthorized"
    error_title = "VAST Unauthorized"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class VASTInvalidParameterError(VASTAPIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/vast/invalid-parameter"
    error_title = "VAST Invalid Parameter"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class VASTNotFoundError(VASTAPIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/vast/not-found"
    error_title = "VAST Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VASTClusterNotFoundError(VASTAPIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/vast/cluster-not-found"
    error_title = "VAST Cluster Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VASTQuotaAlreadyExistsError(web.HTTPConflict, VASTAPIError):
    error_type = "https://api.backend.ai/probs/storage/vast/quota-already-exists"
    error_title = "VAST Quota Already Exists"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class VASTCapacityNotFoundError(VASTAPIError):
    error_type = "https://api.backend.ai/probs/storage/vast/capacity-not-found"
    error_title = "VAST Capacity Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VASTUnknownError(VASTAPIError):
    error_type = "https://api.backend.ai/probs/storage/vast/unknown"
    error_title = "VAST Unknown Error"
