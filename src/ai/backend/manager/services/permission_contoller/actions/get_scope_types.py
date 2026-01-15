from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class GetScopeTypesAction(RoleAction):
    """Action to get available scope types.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_scope_types"


@dataclass
class GetScopeTypesActionResult(BaseActionResult):
    """Result of getting scope types."""

    scope_types: list[ScopeType]

    @override
    def entity_id(self) -> Optional[str]:
        return None
