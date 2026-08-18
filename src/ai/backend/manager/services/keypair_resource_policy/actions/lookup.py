from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.lookups import (
    KeypairResourcePolicyNameLookup,
)
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow


@dataclass(frozen=True)
class KeypairResourcePolicyNameKey(LookupKey):
    """The catalog name a caller passes instead of the policy's id."""

    name: str

    @override
    def kind(self) -> str:
        return "keypair_resource_policy_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


@dataclass
class LookupKeypairResourcePolicyAction(
    LookupEntityOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Resolve a keypair resource policy's name into the policy it names."""

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_keypair_resource_policy"

    @override
    def lookup_key(self) -> KeypairResourcePolicyNameKey:
        return KeypairResourcePolicyNameKey(name=self.name)

    @override
    def to_lookup(self) -> KeypairResourcePolicyNameLookup:
        return KeypairResourcePolicyNameLookup(name=self.name)
