from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.queriers import BulkRolePermissionQuerier
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
)


@dataclass
class BulkGetPermissionsAction(
    PartialBulkGetFieldOpsAction[PermissionID, RoleID, PermissionRow, PermissionData]
):
    """Read the permission entries the caller named, answering for each one."""

    permission_ids: Sequence[PermissionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_permissions"

    @override
    def field_ids(self) -> Sequence[PermissionID]:
        return tuple(self.permission_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkRolePermissionOwnerAction:
        return LookupBulkRolePermissionOwnerAction(permission_ids=self.permission_ids)

    @override
    def to_querier(self) -> BulkRolePermissionQuerier:
        return BulkRolePermissionQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[PermissionID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            permission_ids=[pid for pid in self.permission_ids if pid in allowed],
        )
