from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import KeyPairResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.queriers import KeyPairResourcePolicyQuerier
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow


@dataclass(frozen=True)
class GetKeyPairResourcePolicyAction(
    GetSingleEntityOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Read one keypair resource policy by its id."""

    policy_id: KeyPairResourcePolicyUUID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_keypair_resource_policy"

    @override
    def to_querier(self) -> KeyPairResourcePolicyQuerier:
        return KeyPairResourcePolicyQuerier(uuid=self.policy_id)
