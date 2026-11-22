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


class InvalidSessionWorkloadError(BackendAIError, web.HTTPBadRequest):
    """A SessionWorkload spec the session controller cannot turn into Pods."""

    error_type = "https://api.backend.ai/probs/kube/invalid-session-workload"
    error_title = "Invalid SessionWorkload spec."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class UnsupportedBaseDistroError(BackendAIError, web.HTTPBadRequest):
    """No kernel runner build matches the image's base distro."""

    error_type = "https://api.backend.ai/probs/kube/unsupported-base-distro"
    error_title = "No kernel runner build matches the image's base distro."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class NodeHelperCommandError(BackendAIError, web.HTTPInternalServerError):
    """A container engine command of the node helper (commit, push) failed."""

    error_type = "https://api.backend.ai/probs/kube/node-helper-command-failed"
    error_title = "The node helper's container engine command failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
