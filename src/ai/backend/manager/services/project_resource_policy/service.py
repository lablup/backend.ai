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
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
    ModifyProjectResourcePolicyActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ProjectResourcePolicyService:
    _project_resource_policy_repository: ProjectResourcePolicyRepository

    def __init__(
        self,
        project_resource_policy_repository: ProjectResourcePolicyRepository,
    ) -> None:
        self._project_resource_policy_repository = project_resource_policy_repository

    async def create_project_resource_policy(
        self, action: CreateProjectResourcePolicyAction
    ) -> CreateProjectResourcePolicyActionResult:
        fields = action.creator.fields_to_store()
        result = await self._project_resource_policy_repository.create(fields)
        return CreateProjectResourcePolicyActionResult(project_resource_policy=result)

    async def modify_project_resource_policy(
        self, action: ModifyProjectResourcePolicyAction
    ) -> ModifyProjectResourcePolicyActionResult:
        name = action.name
        to_update = action.modifier.fields_to_update()
        result = await self._project_resource_policy_repository.update(name, to_update)
        return ModifyProjectResourcePolicyActionResult(project_resource_policy=result)

    async def delete_project_resource_policy(
        self, action: DeleteProjectResourcePolicyAction
    ) -> DeleteProjectResourcePolicyActionResult:
        name = action.name
        result = await self._project_resource_policy_repository.delete(name)
        return DeleteProjectResourcePolicyActionResult(project_resource_policy=result)
