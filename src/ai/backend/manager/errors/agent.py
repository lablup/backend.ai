"""
Agent-related exceptions.
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
from ai.backend.common.types import AgentId


class AgentConnectionUnavailable(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when an Agent connection is unavailable."""

    error_type = "https://api.backend.ai/probs/agent-connection-unavailable"
    error_title = "Agent connection unavailable."

    def __init__(self, agent_id: AgentId, failure_reason: str) -> None:
        self.agent_id = agent_id
        self.failure_reason = failure_reason
        super().__init__(f"Agent {agent_id} connection unavailable: {failure_reason}")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
