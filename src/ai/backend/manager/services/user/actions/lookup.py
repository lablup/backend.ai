from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.user.lookups import UserEmailLookup
from ai.backend.manager.models.user.row import UserRow


@dataclass(frozen=True)
class UserEmailKey(LookupKey):
    """The email a caller passes instead of the user's id."""

    email: str

    @override
    def kind(self) -> str:
        return "user_email"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"email": self.email}


@dataclass
class LookupUserAction(LookupEntityOpsAction[UserRow, UserID]):
    """Resolve a user's email into the user it names."""

    email: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_user"

    @override
    def lookup_key(self) -> UserEmailKey:
        return UserEmailKey(email=self.email)

    @override
    def to_lookup(self) -> UserEmailLookup:
        return UserEmailLookup(email=self.email)
