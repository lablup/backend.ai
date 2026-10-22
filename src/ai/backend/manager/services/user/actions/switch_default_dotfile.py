from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileData


@dataclass(frozen=True)
class SwitchDefaultDotfileAction(BaseSingleEntityAction):
    """Make one of a user's dotfiles the default of its path."""

    user_id: UserID
    dotfile_id: DotfileID

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
        return "switch_default_dotfile"


@dataclass(frozen=True)
class SwitchDefaultDotfileActionResult:
    data: DotfileData
