from __future__ import annotations

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.get_my_user_resource_policy import (
    GetMyUserResourcePolicyAction,
    GetMyUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.get_user_resource_policy import (
    GetUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.search_user_resource_policies import (
    SearchUserResourcePoliciesAction,
)
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService


class UserResourcePolicyProcessors:
    get_user_resource_policy: GlobalActionProcessor[
        GetUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]
    get_my_user_resource_policy: ActionProcessor[
        GetMyUserResourcePolicyAction, GetMyUserResourcePolicyActionResult
    ]
    search_user_resource_policies: GlobalActionProcessor[
        SearchUserResourcePoliciesAction, BatchOpsResult[UserResourcePolicyData]
    ]
    create_user_resource_policy: GlobalActionProcessor[
        CreateUserResourcePolicyAction, CreatedEntityOpsResult[UserResourcePolicyData]
    ]
    modify_user_resource_policy: GlobalActionProcessor[
        ModifyUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]
    delete_user_resource_policy: GlobalActionProcessor[
        DeleteUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]

    def __init__(
        self,
        service: UserResourcePolicyService,
        action_monitors: list[ActionMonitor],
        group: ProcessorGroup[UserResourcePolicyData],
    ) -> None:
        self.get_user_resource_policy = group.global_get_ops(GetUserResourcePolicyAction)
        self.get_my_user_resource_policy = ActionProcessor(
            service.get_my_user_resource_policy, action_monitors
        )
        self.search_user_resource_policies = group.global_search_ops(
            SearchUserResourcePoliciesAction
        )
        self.create_user_resource_policy = group.global_create_ops(CreateUserResourcePolicyAction)
        self.modify_user_resource_policy = group.global_update_ops(ModifyUserResourcePolicyAction)
        self.delete_user_resource_policy = group.global_purge_ops(DeleteUserResourcePolicyAction)
