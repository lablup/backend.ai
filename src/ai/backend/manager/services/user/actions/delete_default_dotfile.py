from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileEntry
from ai.backend.manager.models.dotfile.purgers import DotfileEntryPurger


@dataclass(frozen=True)
class DeleteDefaultDotfileAction(BaseSingleEntityAction):
    """Remove a file from the user's default dotfiles."""

    user_id: UserID
    purger: DotfileEntryPurger

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_default_dotfile"


@dataclass(frozen=True)
class DeleteDefaultDotfileActionResult:
    entries: tuple[DotfileEntry, ...]
