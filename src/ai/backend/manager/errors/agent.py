"""
Agent-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.common import ObjectNotFound


class AgentConnectionUnavailable(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when an Agent connection is unavailable."""

    error_type = "https://api.backend.ai/probs/agent-connection-unavailable"
    error_title = "Agent connection unavailable."

    def __init__(self, agent_id: AgentId, failure_reason: str) -> None:
        self.agent_id = agent_id
        self.failure_reason = failure_reason
        super().__init__(f"Agent {agent_id} connection unavailable: {failure_reason}")

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class AgentAlreadyExited(EntityError, web.HTTPConflict):
    """Raised when an exit is recorded for an agent already in a terminal status."""

    error_type = "https://api.backend.ai/probs/agent-already-exited"
    error_title = "Agent has already exited."

    agent_uuid: AgentUUID

    def __init__(self, agent_uuid: AgentUUID) -> None:
        self.agent_uuid = agent_uuid
        super().__init__(f"Agent {agent_uuid} is already in a terminal status.")

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(AgentEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT)


class AgentHasConflictingSessions(EntityError, web.HTTPConflict):
    """
    Raised when an agent has sessions conflicting with its resource group and
    the caller did not request forced cleanup (the admin must drain first).
    """

    error_type = "https://api.backend.ai/probs/agent-has-conflicting-sessions"
    error_title = "Agent has sessions conflicting with its resource group."

    def __init__(self, agent_id: AgentId, conflicting_count: int) -> None:
        self.agent_id = agent_id
        self.conflicting_count = conflicting_count
        super().__init__(
            f"Agent {agent_id} has {conflicting_count} session(s) conflicting with its "
            "resource group; drain them or retry with force."
        )

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(AgentEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT)


class ConflictingSessionRescheduleNotSupported(BackendAIError, web.HTTPNotImplemented):
    """
    Raised when the RESCHEDULE cleanup policy is requested. Re-enqueueing
    conflicting sessions depends on the RESCHEDULING state from the preemption
    work, which is not yet available; only TERMINATE is implemented.
    """

    error_type = "https://api.backend.ai/probs/conflicting-session-reschedule-not-supported"
    error_title = "Rescheduling conflicting sessions is not supported yet."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class AgentNotFound(EntityError, ObjectNotFound):
    object_name = "agent"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(AgentEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class AgentNotAllocated(BackendAIError, web.HTTPInternalServerError):
    """Raised when a kernel that should be placed carries no agent yet.

    Stays on :class:`BackendAIError`: it reports ``access``, which
    ``ActionOperationType`` has no value for.
    """

    error_type = "https://api.backend.ai/probs/agent-not-allocated"
    error_title = "Agent is not allocated for the kernel."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
