from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.user_role import UserRoleAssignmentID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.queriers import BulkUserRoleQuerier
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.services.permission_contoller.actions.lookup_assignment_owner import (
    LookupBulkRoleAssignmentOwnerAction,
)


@dataclass
class BulkGetRoleAssignmentsAction(
    PartialBulkGetFieldOpsAction[UserRoleAssignmentID, UserID, UserRoleRow, AssignedUserData]
):
    """Read the role assignments the caller named, answering for each one."""

    assignment_ids: Sequence[UserRoleAssignmentID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_role_assignments"

    @override
    def field_ids(self) -> Sequence[UserRoleAssignmentID]:
        return tuple(self.assignment_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkRoleAssignmentOwnerAction:
        return LookupBulkRoleAssignmentOwnerAction(assignment_ids=self.assignment_ids)

    @override
    def to_querier(self) -> BulkUserRoleQuerier:
        return BulkUserRoleQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[UserRoleAssignmentID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            assignment_ids=[aid for aid in self.assignment_ids if aid in allowed],
        )
