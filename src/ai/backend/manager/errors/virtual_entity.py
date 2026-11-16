"""Virtual entity error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = ("VirtualEntityNotFound",)


class VirtualEntityNotFound(BackendAIError, web.HTTPInternalServerError):
    """Raised when a scope's virtual entity is expected to exist but does not.

    A virtual entity is always created alongside any owner scope, so a missing one is
    a server-side data-integrity condition (an invariant violation), not a client
    error — hence 500.
    """

    error_type = "https://api.backend.ai/probs/virtual-entity-not-found"
    error_title = "The virtual entity for the given scope does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
