from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.manager_admin import MANAGER_ADMIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class UpdateAnnouncementAction(BaseGlobalAction):
    """Action to update the announcement."""

    enabled: bool
    message: str | None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MANAGER_ADMIN_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_manager_announcement"


@dataclass
class UpdateAnnouncementActionResult:
    """Result of updating the announcement."""
