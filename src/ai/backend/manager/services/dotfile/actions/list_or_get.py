from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.dotfile.types import DotfileEntityKey, DotfileEntry, DotfileScope

from .base import DotfileAction


@dataclass
class ListOrGetDotfilesAction(DotfileAction):
    """Action to list all dotfiles or get a specific one by path."""

    scope: DotfileScope
    entity_key: DotfileEntityKey
    path: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return str(self.entity_key)


@dataclass
class ListOrGetDotfilesActionResult(BaseActionResult):
    """Result of listing or getting dotfiles.

    If a single dotfile was requested (path specified), ``entries`` contains
    exactly one element.
    """

    entries: list[DotfileEntry]

    @override
    def entity_id(self) -> str | None:
        return None
