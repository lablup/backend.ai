from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.get_user_resource_policy import (
    GetUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.global_search_user_resource_policies import (
    GlobalSearchUserResourcePoliciesAction,
)
from ai.backend.manager.services.user_resource_policy.actions.lookup import (
    LookupUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.purge_user_resource_policy import (
    PurgeUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.update_user_resource_policy import (
    UpdateUserResourcePolicyAction,
)


class UserResourcePolicyProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    global_get: GlobalActionProcessor[
        GetUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]
    lookup: LookupActionProcessor[
        LookupUserResourcePolicyAction, LookupOpsResult[UserResourcePolicyData]
    ]
    global_search: GlobalActionProcessor[
        GlobalSearchUserResourcePoliciesAction, BatchOpsResult[UserResourcePolicyData]
    ]
    global_create: GlobalActionProcessor[
        CreateUserResourcePolicyAction, CreatedEntityOpsResult[UserResourcePolicyData]
    ]
    global_update: GlobalActionProcessor[
        UpdateUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]

    def __init__(self, group: ProcessorGroup[UserResourcePolicyData]) -> None:
        self.global_get = group.global_get_ops(GetUserResourcePolicyAction)
        self.lookup = group.lookup_ops(LookupUserResourcePolicyAction)
        self.global_search = group.global_search_ops(GlobalSearchUserResourcePoliciesAction)
        self.global_create = group.global_create_ops(CreateUserResourcePolicyAction)
        self.global_update = group.global_update_ops(UpdateUserResourcePolicyAction)
        self.purge = group.entity_purge_ops(PurgeUserResourcePolicyAction)
