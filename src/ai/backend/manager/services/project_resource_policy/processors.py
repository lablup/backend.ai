from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.get_project_resource_policy import (
    GetProjectResourcePolicyAction,
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

    global_get: GlobalActionProcessor[
        GetProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]
    global_search: GlobalActionProcessor[
        SearchProjectResourcePoliciesAction, BatchOpsResult[ProjectResourcePolicyData]
    ]
    global_create: GlobalActionProcessor[
        CreateProjectResourcePolicyAction, CreatedEntityOpsResult[ProjectResourcePolicyData]
    ]
    global_update: GlobalActionProcessor[
        UpdateProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]

    def __init__(self, group: ProcessorGroup[ProjectResourcePolicyData]) -> None:
        self.global_get = group.global_get_ops(GetProjectResourcePolicyAction)
        self.global_search = group.global_search_ops(SearchProjectResourcePoliciesAction)
        self.global_create = group.global_create_ops(CreateProjectResourcePolicyAction)
        self.global_update = group.global_update_ops(UpdateProjectResourcePolicyAction)
        self.purge = group.entity_purge_ops(PurgeProjectResourcePolicyAction)
