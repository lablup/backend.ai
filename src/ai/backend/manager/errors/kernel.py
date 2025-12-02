"""
Kernel and session-related exceptions.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.json import dump_json

from ..exceptions import AgentError
from .common import ObjectNotFound

if TYPE_CHECKING:
    pass


class KernelNotReady(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/kernel-not-ready"
    error_title = "Kernel not ready."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_READY,
        )


class InvalidSessionId(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-session-id"
    error_title = "Invalid session ID format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class SessionNotFound(ObjectNotFound):
    object_name = "session"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MainKernelNotFound(ObjectNotFound):
    object_name = "main kernel"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KernelNotFound(ObjectNotFound):
    object_name = "kernel"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class TooManySessionsMatched(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-sessions-matched"
    error_title = "Too many sessions matched."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.CONFLICT,
        )

    def __init__(
        self,
        extra_msg: Optional[str] = None,
        extra_data: Optional[dict[str, Any]] = None,
        **kwargs,
    ):
        if extra_data is not None and (matches := extra_data.get("matches", None)) is not None:
            serializable_matches = [
                {
                    "id": str(item["session_id"]),
                    "name": item["session_name"],
                    "status": item["status"].name,
                    "created_at": item["created_at"].isoformat(),
                }
                for item in matches
            ]
            extra_data["matches"] = serializable_matches
        super().__init__(extra_msg, extra_data, **kwargs)


class TooManyKernelsFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-kernels"
    error_title = "There are two or more matching kernels."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.CONFLICT,
        )


class SessionAlreadyExists(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/session-already-exists"
    error_title = "The session already exists but you requested not to reuse existing one."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class QuotaExceeded(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/quota-exceeded"
    error_title = "You have reached your resource limit."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class BackendAgentError(BackendAIError):
    """
    An RFC-7807 error class that wraps agent-side errors.
    """

    _short_type_map = {
        "TIMEOUT": "https://api.backend.ai/probs/agent-timeout",
        "INVALID_INPUT": "https://api.backend.ai/probs/agent-invalid-input",
        "FAILURE": "https://api.backend.ai/probs/agent-failure",
    }

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    def __init__(
        self,
        agent_error_type: str,
        exc_info: Union[str, AgentError, Exception, Mapping[str, Optional[str]], None] = None,
    ):
        super().__init__()
        agent_details: Mapping[str, Optional[str]]
        if not agent_error_type.startswith("https://"):
            agent_error_type = self._short_type_map[agent_error_type.upper()]
        self.args = (
            self.status_code,
            self.reason,
            self.error_type,
            agent_error_type,
        )
        if isinstance(exc_info, str):
            agent_details = {
                "type": agent_error_type,
                "title": exc_info,
            }
        elif isinstance(exc_info, AgentError):
            e = cast(AgentError, exc_info)
            agent_details = {
                "type": agent_error_type,
                "title": "Agent-side exception occurred.",
                "exception": e.exc_repr,
            }
        elif isinstance(exc_info, Exception):
            agent_details = {
                "type": agent_error_type,
                "title": "Unexpected exception ocurred.",
                "exception": repr(exc_info),
            }
        elif isinstance(exc_info, Mapping):
            agent_details = exc_info
        else:
            agent_details = {
                "type": agent_error_type,
                "title": None if exc_info is None else str(exc_info),
            }
        self.agent_details = agent_details
        self.agent_error_type = agent_error_type
        self.agent_error_title = agent_details["title"]
        self.agent_exception = agent_details.get("exception", "")
        self.body = dump_json({
            "type": self.error_type,
            "title": self.error_title,
            "agent-details": agent_details,
        })

    def __str__(self):
        if self.agent_exception:
            return f"{self.agent_error_title} ({self.agent_exception})"
        return f"{self.agent_error_title}"

    def __repr__(self):
        if self.agent_exception:
            return f"<{type(self).__name__}: {self.agent_error_title} ({self.agent_exception})>"
        return f"<{type(self).__name__}: {self.agent_error_title}>"

    def __reduce__(self):
        return (type(self), (self.agent_error_type, self.agent_details))


class KernelCreationFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-creation-failed"
    error_title = "Kernel creation has failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelDestructionFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-destruction-failed"
    error_title = "Kernel destruction has failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelRestartFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-restart-failed"
    error_title = "Kernel restart has failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelExecutionFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-execution-failed"
    error_title = "Executing user code in the kernel has failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class InvalidStreamMode(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-stream-mode"
    error_title = "Invalid or missing stream mode parameter."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidSessionData(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-session-data"
    error_title = "Session data has an invalid type or format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class InvalidKernelConfig(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-kernel-config"
    error_title = "Invalid kernel configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class IdlePolicyNotFound(ObjectNotFound):
    object_name = "idle policy"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidKernelStatus(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/invalid-kernel-status"
    error_title = "Invalid kernel status for this operation."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
