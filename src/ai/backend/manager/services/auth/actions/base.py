from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


class UserGlobalAction(BaseGlobalAction):
    """Base for an operation reaching the user rows, or their login rows, at large.

    Names no id: the operation either spans every user, or runs before the caller is
    known and produces the subject it names.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()


@dataclass(frozen=True)
class UserEntityAction(BaseSingleEntityAction):
    """Base for an operation on one user's account, credentials or login rows."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id
