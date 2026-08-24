from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.client_ip_masking import CLIENT_IP_MASKING_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpsertGlobalOpsAction
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.client_ip_masking.upserters import ClientIPMaskingPolicyUpserter


@dataclass
class UpsertClientIPMaskingPolicyAction(
    UpsertGlobalOpsAction[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Set the masking one target gets.

    Upsert-shaped: a target holds one policy, so the caller names the target rather
    than looking up whether a row is already there.
    """

    target_type: ClientIPMaskingTarget
    mode: ClientIPMaskingMode

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return CLIENT_IP_MASKING_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upsert_client_ip_masking_policy"

    @override
    def to_upserter(self) -> ClientIPMaskingPolicyUpserter:
        return ClientIPMaskingPolicyUpserter(target_type=self.target_type, mode=self.mode)
