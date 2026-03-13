from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.dotfile.types import DotfileEntityKey, DotfileScope

from .base import DotfileAction


@dataclass
class DeleteDotfileAction(DotfileAction):
    """Action to delete a dotfile."""

    scope: DotfileScope
    entity_key: DotfileEntityKey
    path: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return str(self.entity_key)


@dataclass
class DeleteDotfileActionResult(BaseActionResult):
    """Result of deleting a dotfile."""

    @override
    def entity_id(self) -> str | None:
        return None
