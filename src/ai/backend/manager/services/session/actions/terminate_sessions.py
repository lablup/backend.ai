from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class TerminateSessionsAction(SessionAction):
    """Terminate one or more sessions by their IDs."""

    session_ids: list[SessionId]
    forced: bool

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class TerminateSessionsActionResult(BaseActionResult):
    """Result of batch session termination."""

    cancelled: list[UUID] = field(default_factory=list)
    terminating: list[UUID] = field(default_factory=list)
    force_terminated: list[UUID] = field(default_factory=list)
    skipped: list[UUID] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
