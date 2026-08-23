"""Secret encryption exceptions."""

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


class InvalidEncryptedSecretFormat(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-encrypted-secret-format"
    error_title = "The stored secret does not follow the encrypted secret format."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SECRET,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class UnsupportedSecretFormatVersion(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unsupported-secret-format-version"
    error_title = "The stored secret uses a format version this build cannot read."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SECRET,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class UnknownSecretKeyProvider(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unknown-secret-key-provider"
    error_title = "The stored secret names a key provider that is not configured."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SECRET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
