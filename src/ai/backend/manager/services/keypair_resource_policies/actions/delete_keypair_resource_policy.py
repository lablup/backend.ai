from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.services.keypair_resource_policies.base import KeypairResourcePolicyAction


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
    # TODO: 리턴 타입 만들 것.
    keypair_resource_policy: KeyPairResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
