from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.v2.field.lookup import LookupFieldByKeyOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.keypair.lookups import KeypairAccessKeyLookup
from ai.backend.manager.services.user.actions.lookup_keypair_owner import KeypairAccessKeyLookupKey


@dataclass
class LookupKeypairByAccessKeyAction(LookupFieldByKeyOpsAction[KeyPairID, UserID]):
    """Resolve an access key into the keypair it names, and the user that owns it."""

    access_key: AccessKey

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_keypair"

    @override
    def lookup_key(self) -> LookupKey:
        return KeypairAccessKeyLookupKey(self.access_key)

    @override
    def to_field_lookup(self) -> KeypairAccessKeyLookup:
        return KeypairAccessKeyLookup(access_key=self.access_key)
