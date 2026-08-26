"""What every RBAC action shares.

Two shapes sit here. A link between entities neither of which contains the other is
`relation`-shaped and names both scopes; putting a user in an organization, or moving
the roles they hold in it, is the contained case and is `scope`-shaped.

Both are abstract in what they write: the table and its columns come from the spec the
declaring domain carries on its own subclass. What is not domain-specific is the
permission, which is what these bases fix.

Design rationale: `proposals/BEP-1075-entity-relation-operations.md` and BEP-1076.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    ScopeRef,
    ScopeType,
)
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult

__all__ = (
    "BaseEntityRelationAction",
    "BaseOrganizationMemberAction",
    "OrganizationMemberActionResult",
)


@dataclass(frozen=True)
class BaseEntityRelationAction(BaseRelationAction, ABC):
    """A link between two entities, or its removal.

    Both scopes have to permit the run: you must be able to touch both to put them in a
    relation. Which side is `left` is the declaring domain's choice and carries no
    meaning here — the row stands between the two.
    """

    left: EntityIdentifier
    right: EntityIdentifier

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (
            ScopeRef(scope_type=ScopeType(self.left.entity_type()), scope_id=self.left),
            ScopeRef(scope_type=ScopeType(self.right.entity_type()), scope_id=self.right),
        )


@dataclass(frozen=True)
class BaseOrganizationMemberAction(BaseScopeAction, ABC):
    """A change to what a user is within an organization.

    The contained case: the organization is the scope, and the user is what the run acts
    on inside it. One scope, not two — a member is inside the organization, so reaching
    the organization is what the permission asks about.
    """

    organization: EntityIdentifier
    user_id: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (
            ScopeRef(
                scope_type=ScopeType(self.organization.entity_type()), scope_id=self.organization
            ),
        )


@dataclass(frozen=True)
class OrganizationMemberActionResult(BaseScopeActionResult):
    """The member the run was about, which the audit trail is keyed on."""

    user_id: UserID

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.user_id,)
