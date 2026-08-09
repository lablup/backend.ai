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
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.get_project_resource_policy import (
    GetProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.search_project_resource_policies import (
    SearchProjectResourcePoliciesAction,
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
    modify_project_resource_policy: GlobalActionProcessor[
        ModifyProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]
    delete_project_resource_policy: GlobalActionProcessor[
        DeleteProjectResourcePolicyAction, EntityOpsResult[ProjectResourcePolicyData]
    ]

    def __init__(self, group: ProcessorGroup[ProjectResourcePolicyData]) -> None:
        self.get_project_resource_policy = group.global_get_ops(GetProjectResourcePolicyAction)
        self.search_project_resource_policies = group.global_search_ops(
            SearchProjectResourcePoliciesAction
        )
        self.create_project_resource_policy = group.global_create_ops(
            CreateProjectResourcePolicyAction
        )
        self.modify_project_resource_policy = group.global_update_ops(
            ModifyProjectResourcePolicyAction
        )
        self.delete_project_resource_policy = group.global_purge_ops(
            DeleteProjectResourcePolicyAction
        )
