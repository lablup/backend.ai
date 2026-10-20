from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.queriers import BulkClientIPMaskingPolicyQuerier
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow


@dataclass
class BulkGetClientIPMaskingPoliciesAction(
    PartialBulkGetEntityOpsAction[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Read the client IP masking policies the caller named, one permission check per policy."""

    ids: Sequence[ClientIPMaskingPolicyID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_client_ip_masking_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkClientIPMaskingPolicyQuerier:
        return BulkClientIPMaskingPolicyQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
