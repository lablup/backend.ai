from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import DotfileAction


@dataclass
class UpdateBootstrapScriptAction(DotfileAction):
    """Action to update a user's bootstrap script."""

    access_key: str
    script: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return self.access_key


@dataclass
class UpdateBootstrapScriptActionResult(BaseActionResult):
    """Result of updating a bootstrap script."""

    @override
    def entity_id(self) -> str | None:
        return None
