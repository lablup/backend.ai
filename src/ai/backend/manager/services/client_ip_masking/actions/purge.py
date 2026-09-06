from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.purgers import ClientIPMaskingPolicyPurger
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow


@dataclass
class PurgeClientIPMaskingPolicyAction(
    PurgeEntityOpsAction[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Drop one target's policy so it falls back to ``default``.

    Purge-shaped: the table carries no lifecycle column, so removing a policy has
    always been the row leaving the table.
    """

    id: ClientIPMaskingPolicyID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_client_ip_masking_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> ClientIPMaskingPolicyPurger:
        return ClientIPMaskingPolicyPurger(policy_id=self.id)
