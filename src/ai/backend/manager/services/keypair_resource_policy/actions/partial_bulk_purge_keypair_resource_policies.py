from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_policy import KeyPairResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.purgers import KeyPairResourcePolicyPurger
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow


@dataclass(frozen=True)
class PartialBulkPurgeKeypairResourcePoliciesAction(
    PartialBulkPurgeEntityOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Remove the named keypair resource policies, answering for each one."""

    ids: Sequence[KeyPairResourcePolicyUUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_keypair_resource_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, KeyPairResourcePolicyPurger]:
        return {
            policy_id: KeyPairResourcePolicyPurger(policy_id=policy_id) for policy_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[policy_id for policy_id in self.ids if policy_id in allowed])
