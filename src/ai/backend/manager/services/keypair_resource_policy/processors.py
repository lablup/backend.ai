from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
    CreateKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
    DeleteKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_keypair_resource_policy import (
    GetKeypairResourcePolicyAction,
    GetKeypairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_my_keypair_resource_policy import (
    GetMyKeypairResourcePolicyAction,
    GetMyKeypairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
    ModifyKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.search_keypair_resource_policies import (
    SearchKeypairResourcePoliciesAction,
    SearchKeypairResourcePoliciesActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.service import (
    KeypairResourcePolicyService,
)


class KeypairResourcePolicyProcessors(AbstractProcessorPackage):
    get_keypair_resource_policy: ActionProcessor[
        GetKeypairResourcePolicyAction, GetKeypairResourcePolicyActionResult
    ]
    get_my_keypair_resource_policy: ActionProcessor[
        GetMyKeypairResourcePolicyAction, GetMyKeypairResourcePolicyActionResult
    ]
    search_keypair_resource_policies: ActionProcessor[
        SearchKeypairResourcePoliciesAction, SearchKeypairResourcePoliciesActionResult
    ]
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
        self,
        service: KeypairResourcePolicyService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.get_keypair_resource_policy = ActionProcessor(
            service.get_keypair_resource_policy, action_monitors
        )
        self.get_my_keypair_resource_policy = ActionProcessor(
            service.get_my_keypair_resource_policy, action_monitors
        )
        self.search_keypair_resource_policies = ActionProcessor(
            service.search_keypair_resource_policies, action_monitors
        )
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
            GetKeypairResourcePolicyAction.spec(),
            GetMyKeypairResourcePolicyAction.spec(),
            SearchKeypairResourcePoliciesAction.spec(),
            CreateKeyPairResourcePolicyAction.spec(),
            ModifyKeyPairResourcePolicyAction.spec(),
            DeleteKeyPairResourcePolicyAction.spec(),
        ]
