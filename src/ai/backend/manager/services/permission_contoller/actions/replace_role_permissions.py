from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import BulkRolePermissionReplaceResultData
from ai.backend.manager.models.specs.permission import PermissionEntry


@dataclass
class ReplaceRolePermissionsAction(BaseAction):
    role_id: RoleID
    entries: Sequence[PermissionEntry]

    @override
    def entity_id(self) -> str | None:
        return str(self.role_id)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ReplaceRolePermissionsActionResult(BaseActionResult):
    data: BulkRolePermissionReplaceResultData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.role_id)
