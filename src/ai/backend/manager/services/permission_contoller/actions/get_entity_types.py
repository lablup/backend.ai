from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class GetEntityTypesAction(RoleAction):
    """Action to get available entity types.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_entity_types"


@dataclass
class GetEntityTypesActionResult(BaseActionResult):
    """Result of getting entity types."""

    entity_types: list[EntityType]

    @override
    def entity_id(self) -> str | None:
        return None
