import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.project_resource_policy.repository import (
    ProjectResourcePolicyRepository,
)
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
    CreateProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
    DeleteProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.get_project_resource_policy import (
    GetProjectResourcePolicyAction,
    GetProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
    ModifyProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.search_project_resource_policies import (
    SearchProjectResourcePoliciesAction,
    SearchProjectResourcePoliciesActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ProjectResourcePolicyService:
    _project_resource_policy_repository: ProjectResourcePolicyRepository

    def __init__(
        self,
        project_resource_policy_repository: ProjectResourcePolicyRepository,
    ) -> None:
        self._project_resource_policy_repository = project_resource_policy_repository

    async def get_project_resource_policy(
        self, action: GetProjectResourcePolicyAction
    ) -> GetProjectResourcePolicyActionResult:
        result = await self._project_resource_policy_repository.get_by_name(action.name)
        return GetProjectResourcePolicyActionResult(project_resource_policy=result)

    async def search_project_resource_policies(
        self, action: SearchProjectResourcePoliciesAction
    ) -> SearchProjectResourcePoliciesActionResult:
        result = await self._project_resource_policy_repository.search(action.querier)
        return SearchProjectResourcePoliciesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create_project_resource_policy(
        self, action: CreateProjectResourcePolicyAction
    ) -> CreateProjectResourcePolicyActionResult:
        result = await self._project_resource_policy_repository.create(action.creator)
        return CreateProjectResourcePolicyActionResult(project_resource_policy=result)

    async def modify_project_resource_policy(
        self, action: ModifyProjectResourcePolicyAction
    ) -> ModifyProjectResourcePolicyActionResult:
        result = await self._project_resource_policy_repository.update(action.updater)
        return ModifyProjectResourcePolicyActionResult(project_resource_policy=result)

    async def delete_project_resource_policy(
        self, action: DeleteProjectResourcePolicyAction
    ) -> DeleteProjectResourcePolicyActionResult:
        name = action.name
        result = await self._project_resource_policy_repository.delete(name)
        return DeleteProjectResourcePolicyActionResult(project_resource_policy=result)
