from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
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
from ai.backend.manager.services.user_resource_policy.actions.search_user_resource_policies import (
    SearchUserResourcePoliciesAction,
)
from ai.backend.manager.services.user_resource_policy.actions.update_user_resource_policy import (
    UpdateUserResourcePolicyAction,
)


class UserResourcePolicyProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    lookup: LookupActionProcessor[
        LookupUserResourcePolicyAction, LookupOpsResult[UserResourcePolicyData]
    ]
    search: ScopeActionProcessor[
        SearchUserResourcePoliciesAction, ScopedBatchOpsResult[UserResourcePolicyData]
    ]
    global_search: GlobalActionProcessor[
        GlobalSearchUserResourcePoliciesAction, BatchOpsResult[UserResourcePolicyData]
    ]
    global_create: GlobalActionProcessor[
        CreateUserResourcePolicyAction, CreatedEntityOpsResult[UserResourcePolicyData]
    ]
    update: SingleEntityActionProcessor[
        UpdateUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeUserResourcePolicyAction, EntityOpsResult[UserResourcePolicyData]
    ]

    def __init__(self, group: ProcessorGroup[UserResourcePolicyData]) -> None:
        self.lookup = group.lookup_ops(LookupUserResourcePolicyAction)
        self.search = group.scope_search_ops(SearchUserResourcePoliciesAction)
        self.global_search = group.global_search_ops(GlobalSearchUserResourcePoliciesAction)
        self.global_create = group.global_create_ops(CreateUserResourcePolicyAction)
        self.update = group.single_update_ops(UpdateUserResourcePolicyAction)
        self.purge = group.entity_purge_ops(PurgeUserResourcePolicyAction)
