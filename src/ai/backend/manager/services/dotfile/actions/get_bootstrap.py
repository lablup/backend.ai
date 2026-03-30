from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import DotfileAction


@dataclass
class GetBootstrapScriptAction(DotfileAction):
    """Action to get a user's bootstrap script."""

    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.access_key


@dataclass
class GetBootstrapScriptActionResult(BaseActionResult):
    """Result of getting a bootstrap script."""

    script: str

    @override
    def entity_id(self) -> str | None:
        return None
