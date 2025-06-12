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
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
    ModifyUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService


class UserResourcePolicyProcessors(AbstractProcessorPackage):
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
            CreateUserResourcePolicyAction.spec(),
            ModifyUserResourcePolicyAction.spec(),
            DeleteUserResourcePolicyAction.spec(),
        ]
