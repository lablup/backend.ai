from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.base import KeypairResourcePolicyAction


@dataclass
class DeleteKeyPairResourcePolicyAction(KeypairResourcePolicyAction):
    name: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "delete_keypair_resource_policy"


@dataclass
class DeleteKeyPairResourcePolicyActionResult(BaseActionResult):
    keypair_resource_policy: KeyPairResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
