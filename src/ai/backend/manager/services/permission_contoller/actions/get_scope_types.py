from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class GetScopeTypesAction(RoleAction):
    """Action to get available scope types.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetScopeTypesActionResult(BaseActionResult):
    """Result of getting scope types."""

    scope_types: list[ScopeType]

    @override
    def entity_id(self) -> str | None:
        return None
