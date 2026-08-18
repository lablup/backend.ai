from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_policy.updaters import (
    KeyPairResourcePolicyUpdater,
)


@dataclass
class UpdateKeyPairResourcePolicyAction(
    UpdateSingleEntityOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Retune one keypair resource policy.

    Takes both axes: ``policy_id`` is what the operation is answered for, while the
    updater still keys on ``name``, which is the table's primary key until the id
    replaces it.
    """

    policy_id: KeyPairResourcePolicyUUID
    updater: KeyPairResourcePolicyUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_keypair_resource_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def to_updater(self) -> KeyPairResourcePolicyUpdater:
        return self.updater
