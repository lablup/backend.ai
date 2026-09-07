"""Resolution of a binding id into the pair it links."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.idle_checker import (
    IDLE_CHECKER_ENTITY_TYPE,
    IdleCheckerAssignmentID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData


@dataclass(frozen=True)
class IdleCheckerAssignmentIDKey(LookupKey):
    """The row id the API names instead of the pair."""

    assignment_id: IdleCheckerAssignmentID

    @override
    def kind(self) -> str:
        return "idle_checker_assignment_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"assignment_id": str(self.assignment_id)}


@dataclass(frozen=True)
class LookupIdleCheckerAssignmentAction(BaseLookupAction):
    """Resolve a binding id into the scope and checker it links.

    The resolved entity is the checker: a relation read answers with what the relation
    reaches. Resolving costs READ on the checker, which a scope reader holds through
    the scope's govern of it.
    """

    assignment_id: IdleCheckerAssignmentID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return IDLE_CHECKER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_idle_checker_assignment"

    @override
    def lookup_key(self) -> IdleCheckerAssignmentIDKey:
        return IdleCheckerAssignmentIDKey(assignment_id=self.assignment_id)


@dataclass(frozen=True)
class LookupIdleCheckerAssignmentActionResult(BaseLookupActionResult):
    data: IdleCheckerAssignmentData

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.data.idle_checker_id
