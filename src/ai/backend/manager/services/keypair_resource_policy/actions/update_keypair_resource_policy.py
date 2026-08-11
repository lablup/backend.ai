from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.repositories.keypair_resource_policy.updaters import (
    KeyPairResourcePolicyUpdater,
)


@dataclass
class UpdateKeyPairResourcePolicyAction(
    UpdateGlobalOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Retune one keypair resource policy; the name stays the key."""

    updater: KeyPairResourcePolicyUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_update_keypair_resource_policy"

    @override
    def to_updater(self) -> KeyPairResourcePolicyUpdater:
        return self.updater
