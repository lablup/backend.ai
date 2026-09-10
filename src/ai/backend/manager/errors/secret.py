"""Secret encryption exceptions."""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.secret import SecretFieldType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode


class InvalidEncryptedSecretFormat(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-encrypted-secret-format"
    error_title = "The stored secret does not follow the encrypted secret format."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            SecretFieldType(), ActionOperationType.GET, ErrorDetail.INVALID_DATA_FORMAT
        )


class UnsupportedSecretFormatVersion(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unsupported-secret-format-version"
    error_title = "The stored secret uses a format version this build cannot read."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            SecretFieldType(), ActionOperationType.GET, ErrorDetail.INVALID_DATA_FORMAT
        )


class UnknownSecretKeyProvider(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unknown-secret-key-provider"
    error_title = "The stored secret names a key provider that is not configured."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(SecretFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class InvalidSecretKeyMaterial(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-secret-key-material"
    error_title = "A configured secret encryption key is not of a usable size."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SECRET,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class UnknownSecretKeyId(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unknown-secret-key-id"
    error_title = "The stored secret names a key id that is not configured."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(SecretFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class SecretDecryptionFailed(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/secret-decryption-failed"
    error_title = "The secret failed authentication during decryption."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            SecretFieldType(), ActionOperationType.GET, ErrorDetail.INTERNAL_ERROR
        )


class SecretEncryptionMisconfigured(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/secret-encryption-misconfigured"
    error_title = "The secret encryption settings cannot be assembled."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SECRET,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidSecretBinding(FieldError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-secret-binding"
    error_title = "A secret column accepts only a parsed secret value."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            SecretFieldType(), ActionOperationType.CREATE, ErrorDetail.INVALID_PARAMETERS
        )
