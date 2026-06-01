from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import BulkRolePermissionReplaceResultData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.creator import BulkCreator


@dataclass
class ReplaceRolePermissionsAction(BaseAction):
    role_id: uuid.UUID
    creator: BulkCreator[PermissionRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.role_id)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE

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
