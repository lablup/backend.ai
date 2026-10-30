from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_policy import KeyPairResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.queriers import BulkKeyPairResourcePolicyQuerier
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow


@dataclass
class BulkGetKeypairResourcePoliciesAction(
    PartialBulkGetEntityOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Read the keypair resource policies the caller named, one permission check per policy."""

    ids: Sequence[KeyPairResourcePolicyUUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_keypair_resource_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkKeyPairResourcePolicyQuerier:
        return BulkKeyPairResourcePolicyQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
