"""
Keypair-related exceptions.
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


class KeyPairNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/keypair-not-found"
    error_title = "Keypair not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KeyPairAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/keypair-already-exists"
    error_title = "Keypair already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class KeyPairCreationFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/keypair-creation-failed"
    error_title = "Keypair creation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class KeyPairUpdateFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/keypair-update-failed"
    error_title = "Keypair update failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class KeyPairDeletionFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/keypair-deletion-failed"
    error_title = "Keypair deletion failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.DELETE,
            error_detail=ErrorDetail.UNSPECIFIED,
        )


class KeyPairInvalidParameter(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/keypair-invalid-parameter"
    error_title = "Invalid parameter for keypair operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
