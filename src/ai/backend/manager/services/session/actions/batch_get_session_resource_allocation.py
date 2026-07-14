from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import ActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate


@dataclass(frozen=True)
class SessionResourceAllocationTarget(ActionTarget):
    """Bulk-action target identifying a single session by ID."""

    session_id: SessionId

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=str(self.session_id),
        )


@dataclass
class BatchGetSessionResourceAllocationAction(BaseBulkAction[SessionResourceAllocationTarget]):
    """Batch-aggregate resource allocations for one or more sessions.

    Used by the GraphQL DataLoader backing ``SessionV2.resourceAllocation``; the
    session ids originate from already-authorized session nodes.
    """

    session_ids: list[SessionId]

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
        return ActionOperationType.SEARCH

    @override
    def targets(self) -> Sequence[SessionResourceAllocationTarget]:
        return [SessionResourceAllocationTarget(session_id=sid) for sid in self.session_ids]


@dataclass
class BatchGetSessionResourceAllocationActionResult(BaseBulkActionResult):
    data: dict[SessionId, ResourceAllocationAggregate]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(element_type=RBACElementType.SESSION, element_id=str(sid))
            for sid in self.data
        ]
