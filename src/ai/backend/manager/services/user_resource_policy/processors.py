from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
    CreateUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
    DeleteUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.get_user_resource_policy import (
    GetUserResourcePolicyAction,
    GetUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
    ModifyUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.search_user_resource_policies import (
    SearchUserResourcePoliciesAction,
    SearchUserResourcePoliciesActionResult,
)
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService


class UserResourcePolicyProcessors(AbstractProcessorPackage):
    get_user_resource_policy: ActionProcessor[
        GetUserResourcePolicyAction, GetUserResourcePolicyActionResult
    ]
    search_user_resource_policies: ActionProcessor[
        SearchUserResourcePoliciesAction, SearchUserResourcePoliciesActionResult
    ]
    create_user_resource_policy: ActionProcessor[
        CreateUserResourcePolicyAction, CreateUserResourcePolicyActionResult
    ]
    modify_user_resource_policy: ActionProcessor[
        ModifyUserResourcePolicyAction, ModifyUserResourcePolicyActionResult
    ]
    delete_user_resource_policy: ActionProcessor[
        DeleteUserResourcePolicyAction, DeleteUserResourcePolicyActionResult
    ]

    def __init__(
        self, service: UserResourcePolicyService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.get_user_resource_policy = ActionProcessor(
            service.get_user_resource_policy, action_monitors
        )
        self.search_user_resource_policies = ActionProcessor(
            service.search_user_resource_policies, action_monitors
        )
        self.create_user_resource_policy = ActionProcessor(
            service.create_user_resource_policy, action_monitors
        )
        self.modify_user_resource_policy = ActionProcessor(
            service.modify_user_resource_policy, action_monitors
        )
        self.delete_user_resource_policy = ActionProcessor(
            service.delete_user_resource_policy, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetUserResourcePolicyAction.spec(),
            SearchUserResourcePoliciesAction.spec(),
            CreateUserResourcePolicyAction.spec(),
            ModifyUserResourcePolicyAction.spec(),
            DeleteUserResourcePolicyAction.spec(),
        ]
