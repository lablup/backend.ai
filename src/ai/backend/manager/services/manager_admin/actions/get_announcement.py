from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.manager_admin import MANAGER_ADMIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class GetAnnouncementAction(BaseGlobalAction):
    """Action to get the current announcement."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MANAGER_ADMIN_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_manager_announcement"


@dataclass
class GetAnnouncementActionResult:
    """Result of getting the announcement."""

    enabled: bool
    message: str
