from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldByKeyOpsAction
from ai.backend.manager.models.keypair.lookups import KeypairAccessKeysLookup
from ai.backend.manager.services.user.actions.lookup_keypair_owner import KeypairAccessKeyLookupKey


@dataclass
class BulkLookupKeypairsAction(LookupBulkFieldByKeyOpsAction[AccessKey, KeyPairID, UserID]):
    """Resolve several access keys into the keypairs they name."""

    access_keys: Sequence[AccessKey]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_keypairs"

    @override
    def keys(self) -> Sequence[AccessKey]:
        return tuple(self.access_keys)

    @override
    def to_lookup_key(self, key: AccessKey) -> KeypairAccessKeyLookupKey:
        return KeypairAccessKeyLookupKey(key)

    @override
    def to_field_lookup(self) -> KeypairAccessKeysLookup:
        return KeypairAccessKeysLookup()
