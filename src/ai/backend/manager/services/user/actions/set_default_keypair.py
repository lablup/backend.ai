from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class SetMyDefaultKeypairAction(BaseSingleEntityAction):
    """Move the current user's default marker onto one of their keypairs.

    The entity is the user, not the keypair: the marker is unique per user, so the
    operation reads as "this user's default becomes X" and touches two keypair rows.
    """

    user_id: UserID
    access_key: AccessKey

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "set_my_default_keypair"

    @override
    def entity_id(self) -> EntityID:
        return self.user_id


@dataclass
class SetMyDefaultKeypairActionResult:
    access_key: AccessKey
