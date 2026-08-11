from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
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

    get_project_resource_policy: GlobalActionProcessor[
        GetProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]
    search_project_resource_policies: GlobalActionProcessor[
        SearchProjectResourcePoliciesAction, BatchOpsResult[ProjectResourcePolicyData]
    ]
    create_project_resource_policy: GlobalActionProcessor[
        CreateProjectResourcePolicyAction, CreatedEntityOpsResult[ProjectResourcePolicyData]
    ]
    update_project_resource_policy: GlobalActionProcessor[
        UpdateProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]
    purge_project_resource_policy: GlobalActionProcessor[
        PurgeProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]

    def __init__(self, group: ProcessorGroup[ProjectResourcePolicyData]) -> None:
        self.get_project_resource_policy = group.global_get_ops(GetProjectResourcePolicyAction)
        self.search_project_resource_policies = group.global_search_ops(
            SearchProjectResourcePoliciesAction
        )
        self.create_project_resource_policy = group.global_create_ops(
            CreateProjectResourcePolicyAction
        )
        self.update_project_resource_policy = group.global_update_ops(
            UpdateProjectResourcePolicyAction
        )
        self.purge_project_resource_policy = group.global_purge_ops(
            PurgeProjectResourcePolicyAction
        )
