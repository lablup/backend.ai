from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.dotfile.types import DotfileEntityKey, DotfileScope

from .base import DotfileAction


@dataclass
class CreateDotfileAction(DotfileAction):
    """Action to create a dotfile in a domain, group, or user scope."""

    scope: DotfileScope
    entity_key: DotfileEntityKey
    path: str
    data: str
    permission: str
    # For USER scope: needed for vFolder conflict check
    user_uuid: uuid.UUID | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return str(self.entity_key)


@dataclass
class CreateDotfileActionResult(BaseActionResult):
    """Result of creating a dotfile."""

    @override
    def entity_id(self) -> str | None:
        return None
