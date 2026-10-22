from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.purgers import ClientIPMaskingPolicyPurger
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow


@dataclass(frozen=True)
class PartialBulkPurgeClientIPMaskingPoliciesAction(
    PartialBulkPurgeEntityOpsAction[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Drop the named policies so their targets fall back to ``default``, answering for each one."""

    ids: Sequence[ClientIPMaskingPolicyID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_client_ip_masking_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, ClientIPMaskingPolicyPurger]:
        return {
            policy_id: ClientIPMaskingPolicyPurger(policy_id=policy_id) for policy_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[policy_id for policy_id in self.ids if policy_id in allowed])
