from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.actions.base import (
    KeypairResourcePolicyAction,
)


@dataclass
class GetKeypairResourcePolicyAction(KeypairResourcePolicyAction):
    name: str

    @override
    def entity_id(self) -> str | None:
        return self.name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetKeypairResourcePolicyActionResult(BaseActionResult):
    data: KeyPairResourcePolicyData

    @override
    def entity_id(self) -> str | None:
        return self.data.name
