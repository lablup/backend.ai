from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
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
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.lookup import (
    LookupProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.purge_project_resource_policy import (
    PurgeProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.search_project_resource_policies import (
    SearchProjectResourcePoliciesAction,
)
from ai.backend.manager.services.project_resource_policy.actions.update_project_resource_policy import (
    UpdateProjectResourcePolicyAction,
)


class ProjectResourcePolicyProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    lookup: LookupActionProcessor[
        LookupProjectResourcePolicyAction, LookupOpsResult[ProjectResourcePolicyData]
    ]
    global_search: GlobalActionProcessor[
        SearchProjectResourcePoliciesAction, BatchOpsResult[ProjectResourcePolicyData]
    ]
    global_create: GlobalActionProcessor[
        CreateProjectResourcePolicyAction, CreatedEntityOpsResult[ProjectResourcePolicyData]
    ]
    update: SingleEntityActionProcessor[
        UpdateProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]

    def __init__(self, group: ProcessorGroup[ProjectResourcePolicyData]) -> None:
        self.lookup = group.lookup_ops(LookupProjectResourcePolicyAction)
        self.global_search = group.global_search_ops(SearchProjectResourcePoliciesAction)
        self.global_create = group.global_create_ops(CreateProjectResourcePolicyAction)
        self.update = group.single_update_ops(UpdateProjectResourcePolicyAction)
        self.purge = group.entity_purge_ops(PurgeProjectResourcePolicyAction)
