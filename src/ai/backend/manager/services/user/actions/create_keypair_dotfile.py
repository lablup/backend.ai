from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileEntry


@dataclass(frozen=True)
class CreateKeypairDotfileAction(BaseSingleEntityAction):
    """Add one dotfile to a keypair.

    A dotfile is a column of the keypair row, which belongs to a user, so the
    operation is answered for by that user.
    """

    user_id: UserID
    access_key: AccessKey
    entry: DotfileEntry

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
        return "create_keypair_dotfile"


@dataclass(frozen=True)
class CreateKeypairDotfileActionResult:
    entries: tuple[DotfileEntry, ...]
