from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import ActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass(frozen=True)
class SessionTerminationTarget(ActionTarget):
    """Bulk-action target identifying a single session by ID."""

    session_id: SessionId

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=str(self.session_id),
        )


@dataclass
class TerminateSessionsAction(BaseBulkAction[SessionTerminationTarget]):
    """Terminate one or more sessions by their IDs.

    Each session is validated independently by the bulk RBAC validator; any
    denial fails the whole bulk action.
    """

    session_ids: list[SessionId]
    forced: bool

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def targets(self) -> Sequence[SessionTerminationTarget]:
        return [SessionTerminationTarget(session_id=sid) for sid in self.session_ids]


@dataclass
class TerminateSessionsActionResult(BaseBulkActionResult):
    """Result of bulk session termination."""

    cancelled: list[SessionId] = field(default_factory=list)
    terminating: list[SessionId] = field(default_factory=list)
    force_terminated: list[SessionId] = field(default_factory=list)
    skipped: list[SessionId] = field(default_factory=list)

    @override
    def element_refs(self) -> list[RBACElementRef]:
        ids: list[SessionId] = [
            *self.cancelled,
            *self.terminating,
            *self.force_terminated,
            *self.skipped,
        ]
        return [
            RBACElementRef(element_type=RBACElementType.SESSION, element_id=str(sid)) for sid in ids
        ]
