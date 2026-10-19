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


class CniPluginNotInstalled(BackendAIError, web.HTTPInternalServerError):
    """Raised when a session's network config names a CNI plugin this agent has not loaded."""

    error_type = "https://api.backend.ai/probs/agent/cni-plugin-not-installed"
    error_title = "The session's network plugin is not installed on this agent."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )
