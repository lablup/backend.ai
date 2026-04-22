from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import EntityType, OperationType, RBACElementType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class ResolveEffectivePermissionsAction(RoleAction):
    """Action to resolve effective permissions per entity for a given user.

    Given a user ID, an element type, and a list of entity IDs, returns the
    set of permitted operations per entity by traversing the scope chain and
    evaluating all role/permission assignments.
    """

    user_id: UUID
    target_element_type: RBACElementType
    target_entity_ids: list[str]
    permission_entity_type: EntityType | None = None

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveEffectivePermissionsActionResult(BaseActionResult):
    """Result containing the effective permissions per entity."""

    permissions: dict[str, set[OperationType]] = field(default_factory=dict)

    @override
    def entity_id(self) -> str | None:
        return None
