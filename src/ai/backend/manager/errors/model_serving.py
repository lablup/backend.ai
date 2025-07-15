"""
Model serving-related exceptions.
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


class ModelServingNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/model-serving-not-found"
    error_title = "Model serving not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelServingAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/model-serving-already-exists"
    error_title = "Model serving already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ModelServingCreationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/model-serving-creation-failed"
    error_title = "Model serving creation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class ModelServingUpdateFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/model-serving-update-failed"
    error_title = "Model serving update failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class ModelServingDeletionFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/model-serving-deletion-failed"
    error_title = "Model serving deletion failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.DELETE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class ModelServingInvalidParameter(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/model-serving-invalid-parameter"
    error_title = "Invalid parameter for model serving operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class EndpointNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/endpoint-not-found"
    error_title = "Endpoint not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/endpoint-already-exists"
    error_title = "Endpoint already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVING,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )