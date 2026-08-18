from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.keypair.lookups import KeypairOwnerLookup


@dataclass(frozen=True)
class KeyPairIDLookupKey(LookupKey):
    """A keypair row's id, resolved into the user that owns it."""

    keypair_id: KeyPairID

    @override
    def kind(self) -> str:
        return "keypair_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.keypair_id)}


@dataclass
class LookupKeypairOwnerAction(LookupFieldOwnerOpsAction[KeyPairID, UserID]):
    """The user a keypair belongs to."""

    keypair_id: KeyPairID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_keypair_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return KeyPairIDLookupKey(self.keypair_id)

    @override
    def field_id(self) -> KeyPairID:
        return self.keypair_id

    @override
    def to_owner_lookup(self) -> KeypairOwnerLookup:
        return KeypairOwnerLookup()


@dataclass
class LookupBulkKeypairOwnerAction(LookupBulkFieldOwnerOpsAction[KeyPairID, UserID]):
    """The users several keypairs belong to."""

    keypair_ids: Sequence[KeyPairID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_keypair_owner"

    @override
    def to_lookup_key(self, field_id: KeyPairID) -> LookupKey:
        return KeyPairIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[KeyPairID]:
        return tuple(self.keypair_ids)

    @override
    def to_owner_lookup(self) -> KeypairOwnerLookup:
        return KeypairOwnerLookup()
