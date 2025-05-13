from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.actions.base import (
    KeypairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.types import KeyPairResourcePolicyCreator


@dataclass
class CreateKeyPairResourcePolicyAction(KeypairResourcePolicyAction):
    creator: KeyPairResourcePolicyCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateKeyPairResourcePolicyActionResult(BaseActionResult):
    keypair_resource_policy: KeyPairResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
