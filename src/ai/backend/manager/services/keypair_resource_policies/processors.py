from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.keypair_resource_policies.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
    CreateKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policies.service import (
    KeypairResourcePolicyService,
)


class KeypairResourcePolicyProcessors:
    create_keypair_resource_policy: ActionProcessor[
        CreateKeyPairResourcePolicyAction, CreateKeyPairResourcePolicyActionResult
    ]

    def __init__(self, service: KeypairResourcePolicyService) -> None:
        self.create_keypair_resource_policy = ActionProcessor(
            service.create_keypair_resource_policy
        )
