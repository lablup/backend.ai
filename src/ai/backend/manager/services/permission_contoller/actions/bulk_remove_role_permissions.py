from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.actions.v2.field.ops import PartialBulkPurgeFieldOpsAction
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
)


@dataclass(frozen=True)
class BulkRemoveRolePermissionsAction(
    PartialBulkPurgeFieldOpsAction[PermissionID, RoleID, PermissionRow, PermissionData]
):
    """Drop the named permission entries, answering for each one.

    The entries may belong to different roles; every one of those roles answers for
    the removal of the entries it holds.
    """

    permission_ids: Sequence[PermissionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_remove_role_permissions"

    @override
    def field_ids(self) -> Sequence[PermissionID]:
        return tuple(self.permission_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkRolePermissionOwnerAction:
        return LookupBulkRolePermissionOwnerAction(permission_ids=self.permission_ids)

    @override
    def to_purgers(self) -> Mapping[PermissionID, RolePermissionPurger]:
        return {
            permission_id: RolePermissionPurger(permission_id=permission_id)
            for permission_id in self.permission_ids
        }

    @override
    def narrowed_to(self, field_ids: Sequence[PermissionID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            permission_ids=[
                permission_id for permission_id in self.permission_ids if permission_id in allowed
            ],
        )
