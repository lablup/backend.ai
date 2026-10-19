from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileEntry
from ai.backend.manager.models.dotfile.creators import DotfileEntryCreator


@dataclass(frozen=True)
class CreateDotfileAction(BaseSingleEntityAction):
    """Add a dotfile under the user the creator names."""

    creator: DotfileEntryCreator

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.creator.owner

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_dotfile"


@dataclass(frozen=True)
class CreateDotfileActionResult:
    entries: tuple[DotfileEntry, ...]
