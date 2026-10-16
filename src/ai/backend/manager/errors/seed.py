"""Seed file error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = ("InvalidSeedDocument", "SeedKindOutOfOrder")


class InvalidSeedDocument(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-seed-document"
    error_title = "The seed file is not valid."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class SeedKindOutOfOrder(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/seed-kind-out-of-order"
    error_title = "A relation seed kind is declared before an entity seed kind."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
