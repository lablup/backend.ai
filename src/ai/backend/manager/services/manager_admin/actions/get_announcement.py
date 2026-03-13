from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ManagerAdminAction


@dataclass
class GetAnnouncementAction(ManagerAdminAction):
    """Action to get the current announcement."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetAnnouncementActionResult(BaseActionResult):
    """Result of getting the announcement."""

    enabled: bool
    message: str

    @override
    def entity_id(self) -> str | None:
        return None
