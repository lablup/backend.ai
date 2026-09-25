from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import BulkLookupEntityOpsAction
from ai.backend.manager.models.rbac_models.user_role.lookups import (
    RoleAssignmentRolesLookup,
    RoleAssignmentUsersLookup,
)

__all__ = (
    "BulkLookupRoleAssignmentRolesAction",
    "BulkLookupRoleAssignmentUsersAction",
    "RoleAssignmentIDKey",
)


@dataclass(frozen=True)
class RoleAssignmentIDKey(LookupKey):
    """The assignment row a request names, which its two end entities are read from."""

    assignment_id: UUID

    @override
    def kind(self) -> str:
        return "role_assignment_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"assignment_id": str(self.assignment_id)}


@dataclass
class BulkLookupRoleAssignmentRolesAction(BulkLookupEntityOpsAction[UUID, RoleID]):
    """Resolve several assignment row ids into the roles they join to.

    An assignment row belongs to neither end, so the scopes answering for a read of it
    are named by the ends themselves. Every authenticated caller may resolve the keys:
    the read that follows is checked against those scopes.
    """

    assignment_ids: Sequence[UUID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_role_assignment_roles"

    @override
    def keys(self) -> Sequence[UUID]:
        return tuple(self.assignment_ids)

    @override
    def to_lookup_key(self, key: UUID) -> RoleAssignmentIDKey:
        return RoleAssignmentIDKey(assignment_id=key)

    @override
    def to_lookup(self) -> RoleAssignmentRolesLookup:
        return RoleAssignmentRolesLookup()


@dataclass
class BulkLookupRoleAssignmentUsersAction(BulkLookupEntityOpsAction[UUID, UserID]):
    """Resolve several assignment row ids into the users they join to.

    The other end of :class:`BulkLookupRoleAssignmentRolesAction`.
    """

    assignment_ids: Sequence[UUID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_role_assignment_users"

    @override
    def keys(self) -> Sequence[UUID]:
        return tuple(self.assignment_ids)

    @override
    def to_lookup_key(self, key: UUID) -> RoleAssignmentIDKey:
        return RoleAssignmentIDKey(assignment_id=key)

    @override
    def to_lookup(self) -> RoleAssignmentUsersLookup:
        return RoleAssignmentUsersLookup()
