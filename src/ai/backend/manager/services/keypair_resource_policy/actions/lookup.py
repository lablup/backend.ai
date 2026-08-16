from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.repositories.keypair_resource_policy.lookups import (
    KeypairResourcePolicyLookup,
)


@dataclass(frozen=True)
class KeypairResourcePolicyUserKey(LookupKey):
    """The user a caller passes instead of the policy's name."""

    user_id: UserID

    @override
    def kind(self) -> str:
        return "keypair_resource_policy_user"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"user_id": str(self.user_id)}


@dataclass
class LookupKeypairResourcePolicyAction(
    LookupEntityOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Resolve a user into the policy their default keypair is subject to."""

    user_id: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_keypair_resource_policy"

    @override
    def lookup_key(self) -> KeypairResourcePolicyUserKey:
        return KeypairResourcePolicyUserKey(user_id=self.user_id)

    @override
    def to_lookup(self) -> KeypairResourcePolicyLookup:
        return KeypairResourcePolicyLookup(user_id=self.user_id)
