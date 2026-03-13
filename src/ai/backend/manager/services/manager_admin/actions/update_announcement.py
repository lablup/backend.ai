from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ManagerAdminAction


@dataclass
class UpdateAnnouncementAction(ManagerAdminAction):
    """Action to update the announcement."""

    enabled: bool
    message: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class UpdateAnnouncementActionResult(BaseActionResult):
    """Result of updating the announcement."""

    @override
    def entity_id(self) -> str | None:
        return None
