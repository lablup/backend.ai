from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.user_role import UserRoleAssignmentID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.rbac_models.user_role.lookups import UserRoleOwnerLookup


@dataclass(frozen=True)
class AssignmentIDLookupKey(LookupKey):
    """An assignment's id, resolved into the user holding the role."""

    assignment_id: UserRoleAssignmentID

    @override
    def kind(self) -> str:
        return "assignment_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.assignment_id)}


@dataclass
class LookupRoleAssignmentOwnerAction(LookupFieldOwnerOpsAction[UserRoleAssignmentID, UserID]):
    """The user a role assignment belongs to."""

    assignment_id: UserRoleAssignmentID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_role_assignment_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return AssignmentIDLookupKey(self.assignment_id)

    @override
    def field_id(self) -> UserRoleAssignmentID:
        return self.assignment_id

    @override
    def to_owner_lookup(self) -> UserRoleOwnerLookup:
        return UserRoleOwnerLookup()


@dataclass
class LookupBulkRoleAssignmentOwnerAction(
    LookupBulkFieldOwnerOpsAction[UserRoleAssignmentID, UserID]
):
    """The users several role assignments belong to."""

    assignment_ids: Sequence[UserRoleAssignmentID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_role_assignment_owner"

    @override
    def to_lookup_key(self, field_id: UserRoleAssignmentID) -> LookupKey:
        return AssignmentIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[UserRoleAssignmentID]:
        return tuple(self.assignment_ids)

    @override
    def to_owner_lookup(self) -> UserRoleOwnerLookup:
        return UserRoleOwnerLookup()
