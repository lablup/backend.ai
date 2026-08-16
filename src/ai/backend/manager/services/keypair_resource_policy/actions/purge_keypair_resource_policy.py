from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.resource_policy import KeyPairResourcePolicyUUID
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.purgers import (
    KeyPairResourcePolicyPurger,
)
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow


@dataclass
class PurgeKeyPairResourcePolicyAction(
    PurgeEntityOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Remove a keypair resource policy.

    Purge-shaped: the table carries no lifecycle column, so deleting one has
    always been the row leaving the table."""

    name: str
    policy_id: KeyPairResourcePolicyUUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_purge_keypair_resource_policy"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> KeyPairResourcePolicyPurger:
        return KeyPairResourcePolicyPurger(name=self.name, policy_id=self.policy_id)
