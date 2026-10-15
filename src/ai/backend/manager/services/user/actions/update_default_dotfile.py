from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileEntry
from ai.backend.manager.models.dotfile.updaters import DotfileEntryUpdater


@dataclass(frozen=True)
class UpdateDefaultDotfileAction(BaseSingleEntityAction):
    """Rewrite a file in the user's default dotfiles."""

    user_id: UserID
    path: str
    updater: DotfileEntryUpdater

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
        return "update_default_dotfile"


@dataclass(frozen=True)
class UpdateDefaultDotfileActionResult:
    entries: tuple[DotfileEntry, ...]
