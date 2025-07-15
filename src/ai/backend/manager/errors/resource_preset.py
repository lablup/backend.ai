"""
Resource preset-related exceptions.
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


class ResourcePresetNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/resource-preset-not-found"
    error_title = "Resource preset not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ResourcePresetAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/resource-preset-already-exists"
    error_title = "Resource preset already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ResourcePresetCreationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/resource-preset-creation-failed"
    error_title = "Resource preset creation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class ResourcePresetUpdateFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/resource-preset-update-failed"
    error_title = "Resource preset update failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class ResourcePresetDeletionFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/resource-preset-deletion-failed"
    error_title = "Resource preset deletion failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.DELETE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class ResourcePresetInvalidParameter(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/resource-preset-invalid-parameter"
    error_title = "Invalid parameter for resource preset operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )