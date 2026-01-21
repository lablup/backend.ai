from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
    CreateKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
    DeleteKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
    ModifyKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.service import (
    KeypairResourcePolicyService,
)


class KeypairResourcePolicyProcessors(AbstractProcessorPackage):
    create_keypair_resource_policy: ActionProcessor[
        CreateKeyPairResourcePolicyAction, CreateKeyPairResourcePolicyActionResult
    ]
    modify_keypair_resource_policy: ActionProcessor[
        ModifyKeyPairResourcePolicyAction, ModifyKeyPairResourcePolicyActionResult
    ]
    delete_keypair_resource_policy: ActionProcessor[
        DeleteKeyPairResourcePolicyAction, DeleteKeyPairResourcePolicyActionResult
    ]

    def __init__(
        self, service: KeypairResourcePolicyService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_keypair_resource_policy = ActionProcessor(
            service.create_keypair_resource_policy, action_monitors
        )
        self.modify_keypair_resource_policy = ActionProcessor(
            service.modify_keypair_resource_policy, action_monitors
        )
        self.delete_keypair_resource_policy = ActionProcessor(
            service.delete_keypair_resource_policy, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateKeyPairResourcePolicyAction.spec(),
            ModifyKeyPairResourcePolicyAction.spec(),
            DeleteKeyPairResourcePolicyAction.spec(),
        ]
