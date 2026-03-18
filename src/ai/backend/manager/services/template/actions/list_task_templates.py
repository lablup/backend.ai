from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class ListTaskTemplatesAction(TemplateAction):
    """Action to list all active task templates."""

    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListTaskTemplatesActionResult(BaseActionResult):
    """Result of listing task templates."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
