from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.idle_checker import IDLE_CHECKER_ENTITY_TYPE, IdleCheckerID
from ai.backend.common.data.entity.types import EntityIdentifier, ScopeRef, ScopeType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction


@dataclass(frozen=True)
class IdleCheckerAssignmentRelationAction(BaseRelationAction):
    """A link or unlink between a scope and an idle checker: the permission is asked
    of both."""

    scope: EntityIdentifier
    idle_checker_id: IdleCheckerID

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (
            ScopeRef(scope_type=ScopeType(self.scope.entity_type()), scope_id=self.scope),
            ScopeRef(scope_type=ScopeType(IDLE_CHECKER_ENTITY_TYPE), scope_id=self.idle_checker_id),
        )
