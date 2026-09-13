from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)
from ai.backend.manager.models.user import UserRole


@dataclass(frozen=True)
class ActingUserKey(LookupKey):
    """No owner named, so the request acts for the caller and nothing keys it."""

    @override
    def kind(self) -> str:
        return "acting_user"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {}


@dataclass(frozen=True)
class OwnerUserEmailKey(LookupKey):
    """The email naming the user a request acts for."""

    email: str

    @override
    def kind(self) -> str:
        return "owner_user_email"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"email": self.email}


@dataclass(frozen=True)
class PublicResolveUserScopeAction(BaseLookupAction):
    owner_user_email: str | None  # None = self

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_resolve_user_scope"

    @override
    def lookup_key(self) -> LookupKey:
        if self.owner_user_email is None:
            return ActingUserKey()
        return OwnerUserEmailKey(email=self.owner_user_email)


@dataclass(frozen=True)
class PublicResolveUserScopeResult(BaseLookupActionResult):
    owner_uuid: UserID
    owner_role: UserRole

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.owner_uuid
