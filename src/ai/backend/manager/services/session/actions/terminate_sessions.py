from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.result import BaseBulkActionResult, BulkEntityResult


@dataclass
class TerminateSessionsAction(BaseBulkAction):
    """Terminate the sessions the caller named.

    Every named session is answered for on its own, which is what the bulk shape
    says; a denial on one fails the run.
    """

    session_ids: list[SessionId]
    forced: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "terminate_sessions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [SessionID(sid) for sid in self.session_ids]


@dataclass
class TerminateSessionsActionResult(BaseBulkActionResult):
    """Result of bulk session termination."""

    cancelled: list[SessionId] = field(default_factory=list)
    terminating: list[SessionId] = field(default_factory=list)
    force_terminated: list[SessionId] = field(default_factory=list)
    skipped: list[SessionId] = field(default_factory=list)

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        def entry(sid: SessionId, description: str) -> BulkEntityResult:
            return BulkEntityResult(
                entity_id=SessionID(sid),
                status=OperationStatus.SUCCESS,
                description=description,
                error_code=None,
            )

        return [
            *(entry(sid, "cancelled") for sid in self.cancelled),
            *(entry(sid, "terminating") for sid in self.terminating),
            *(entry(sid, "force-terminated") for sid in self.force_terminated),
            *(entry(sid, "skipped") for sid in self.skipped),
        ]
