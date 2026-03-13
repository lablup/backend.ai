from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.dotfile.types import DotfileEntityKey, DotfileScope

from .base import DotfileAction


@dataclass
class UpdateDotfileAction(DotfileAction):
    """Action to update an existing dotfile."""

    scope: DotfileScope
    entity_key: DotfileEntityKey
    path: str
    data: str
    permission: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.entity_key)


@dataclass
class UpdateDotfileActionResult(BaseActionResult):
    """Result of updating a dotfile."""

    @override
    def entity_id(self) -> str | None:
        return None
