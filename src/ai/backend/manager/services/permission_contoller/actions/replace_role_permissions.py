from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.permission.role import BulkRolePermissionReplaceResultData
from ai.backend.manager.models.specs.permission import PermissionEntry


@dataclass(frozen=True)
class ReplaceRolePermissionsAction(BaseSingleEntityAction):
    """Put one role's permission set to exactly what the request names."""

    role_id: RoleID
    entries: Sequence[PermissionEntry]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.role_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "replace_role_permissions"


@dataclass(frozen=True)
class ReplaceRolePermissionsActionResult:
    data: BulkRolePermissionReplaceResultData
