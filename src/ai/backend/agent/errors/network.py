"""Exceptions of the agent's runtime side of container networking."""

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


class ContainerSourceUnwired(BackendAIError, web.HTTPInternalServerError):
    """Raised when a container locator is used before its runtime connection is open.

    An unconnected locator would read the node as empty.
    """

    error_type = "https://api.backend.ai/probs/agent/container-source-unwired"
    error_title = "The container locator has no connection to its runtime."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
