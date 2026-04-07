from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass
class AssignUsersByUsernameToProjectAction(BaseSingleEntityAction):
    project_id: UUID
    names: list[str]
    role_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GRANT_READ

    @override
    def target_entity_id(self) -> str:
        return str(self.role_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ROLE, str(self.role_id))

    @override
    def field_data(self) -> FieldData | None:
        return None


@dataclass
class AssignUsersByUsernameToProjectActionResult(BaseSingleEntityActionResult):
    project_id: UUID
    assigned_count: int
    failed_names: list[str]

    @override
    def target_entity_id(self) -> str:
        return str(self.project_id)
