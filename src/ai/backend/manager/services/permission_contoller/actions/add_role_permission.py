from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import CreateFieldOpsAction
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow


@dataclass(frozen=True)
class AddRolePermissionAction(CreateFieldOpsAction[RoleID, PermissionRow, PermissionData]):
    """Add one permission entry to a role, answered for by that role."""

    role_id: RoleID
    creator: RolePermissionCreator

    @override
    @classmethod
    def action_name(cls) -> str:
        return "add_role_permission"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.role_id

    @override
    def owner_id(self) -> RoleID:
        return self.role_id

    @override
    def to_creator(self) -> RolePermissionCreator:
        return self.creator
