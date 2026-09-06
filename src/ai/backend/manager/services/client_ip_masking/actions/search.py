from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.client_ip_masking import CLIENT_IP_MASKING_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.client_ip_masking.searchers import ClientIPMaskingPolicySearcher


@dataclass
class SearchClientIPMaskingPoliciesAction(
    SearchGlobalOpsAction[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Read the masking set for every target."""

    searcher: ClientIPMaskingPolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return CLIENT_IP_MASKING_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_client_ip_masking_policies"

    @override
    def to_searcher(self) -> ClientIPMaskingPolicySearcher:
        return self.searcher
