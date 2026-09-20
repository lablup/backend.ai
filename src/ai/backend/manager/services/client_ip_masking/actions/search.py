from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow


@dataclass(frozen=True)
class SearchClientIPMaskingPoliciesAction(
    GlobalSearcherOpsAction[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Read the masking set for every target."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ClientIPMaskingPolicyEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_client_ip_masking_policies"
