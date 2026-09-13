from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)


@dataclass(frozen=True)
class ActingKeypairKey(LookupKey):
    """No owner access key named, so the request runs on the caller's own keypair."""

    @override
    def kind(self) -> str:
        return "acting_keypair"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {}


@dataclass(frozen=True)
class OwnerAccessKeyKey(LookupKey):
    """The access key naming the keypair a request acts on."""

    access_key: AccessKey

    @override
    def kind(self) -> str:
        return "owner_access_key"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"access_key": self.access_key}


@dataclass(frozen=True)
class PublicResolveAccessKeyScopeAction(BaseLookupAction):
    owner_access_key: str | None  # None = self

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_resolve_access_key_scope"

    @override
    def lookup_key(self) -> LookupKey:
        if self.owner_access_key is None:
            return ActingKeypairKey()
        return OwnerAccessKeyKey(access_key=AccessKey(self.owner_access_key))


@dataclass(frozen=True)
class PublicResolveAccessKeyScopeResult(BaseLookupActionResult):
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.owner_user_id
