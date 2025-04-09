from ai.backend.manager.actions.processor import ActionProcessor
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


class KeypairResourcePolicyProcessors:
    create_keypair_resource_policy: ActionProcessor[
        CreateKeyPairResourcePolicyAction, CreateKeyPairResourcePolicyActionResult
    ]
    modify_keypair_resource_policy: ActionProcessor[
        ModifyKeyPairResourcePolicyAction, ModifyKeyPairResourcePolicyActionResult
    ]
    delete_keypair_resource_policy: ActionProcessor[
        DeleteKeyPairResourcePolicyAction, DeleteKeyPairResourcePolicyActionResult
    ]

    def __init__(self, service: KeypairResourcePolicyService) -> None:
        self.create_keypair_resource_policy = ActionProcessor(
            service.create_keypair_resource_policy
        )
        self.modify_keypair_resource_policy = ActionProcessor(
            service.modify_keypair_resource_policy
        )
        self.delete_keypair_resource_policy = ActionProcessor(
            service.delete_keypair_resource_policy
        )
