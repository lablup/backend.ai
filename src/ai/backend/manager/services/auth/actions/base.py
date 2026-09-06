from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.auth import AUTH_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


class AuthGlobalAction(BaseGlobalAction):
    """Base for an operation over credential or login-session state.

    Names no entity: the caller is not yet known when it runs, or the state it reaches
    spans every user.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AUTH_ENTITY_TYPE


class UserGlobalAction(BaseGlobalAction):
    """Base for an operation reaching the user rows, or their login rows, at large."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE


@dataclass(frozen=True)
class UserEntityAction(BaseSingleEntityAction):
    """Base for an operation on one user's account, credentials or login rows."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id
