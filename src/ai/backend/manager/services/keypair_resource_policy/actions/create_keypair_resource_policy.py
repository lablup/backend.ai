from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import (
    KeyPairResourcePolicyCreator,
)
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow


@dataclass
class CreateKeyPairResourcePolicyAction(
    CreateGlobalOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Register a keypair resource policy."""

    creator: KeyPairResourcePolicyCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_keypair_resource_policy"

    @override
    def to_creator(self) -> KeyPairResourcePolicyCreator:
        return self.creator
