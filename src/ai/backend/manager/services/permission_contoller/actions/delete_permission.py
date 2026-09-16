from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.actions.v2.field.ops import PurgeFieldOpsAction
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupRolePermissionOwnerAction,
)


@dataclass(frozen=True)
class DeletePermissionAction(
    PurgeFieldOpsAction[PermissionID, RoleID, PermissionRow, PermissionData]
):
    """Drop one permission entry, answered for by the role holding it."""

    permission_id: PermissionID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_permission"

    @override
    def to_owner_lookup_action(self) -> LookupRolePermissionOwnerAction:
        return LookupRolePermissionOwnerAction(permission_id=self.permission_id)

    @override
    def to_purger(self) -> RolePermissionPurger:
        return RolePermissionPurger(permission_id=self.permission_id)
