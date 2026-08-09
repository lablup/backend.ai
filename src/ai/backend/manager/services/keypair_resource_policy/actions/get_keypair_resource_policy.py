from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.repositories.keypair_resource_policy.queriers import (
    KeyPairResourcePolicyQuerier,
)


@dataclass
class GetKeypairResourcePolicyAction(
    GetGlobalOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Read one keypair resource policy by name."""

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_get_keypair_resource_policy"

    @override
    def to_querier(self) -> KeyPairResourcePolicyQuerier:
        return KeyPairResourcePolicyQuerier(name=self.name)
