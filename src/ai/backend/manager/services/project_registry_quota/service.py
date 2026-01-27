"""
Registry quota service for managing per-project container registry quotas.

This module was migrated from `ai.backend.manager.service.container_registry.harbor`
and `ai.backend.manager.service.container_registry.base`.

The original code was referenced by:
- api/group (REST API handlers)
- api/gql_legacy/group (GraphQL resolvers)
- api/gql_legacy/container_registry (GraphQL resolvers)

Due to overlapping file structure conflicts between the legacy `service/` package
and the new `services/` package, a direct migration was not possible.
This file is a clean re-implementation following the new services layer patterns.

TODO: After resolving conflicts, consider:
- Removing the legacy service/container_registry/ package
"""

from __future__ import annotations

import logging

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.container_registry.harbor import (
    AbstractPerProjectRegistryQuotaClient,
    HarborAuthArgs,
    HarborProjectInfo,
    PerProjectHarborQuotaClient,
)
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.repositories.project_registry_quota.repository import (
    AbstractProjectRegistryQuotaRepository,
)
from ai.backend.manager.services.project_registry_quota.actions.create_project_registry_quota import (
    CreateProjectRegistryQuotaAction,
    CreateProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.delete_project_registry_quota import (
    DeleteProjectRegistryQuotaAction,
    DeleteProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.read_project_registry_quota import (
    ReadProjectRegistryQuotaAction,
    ReadProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.update_project_registry_quota import (
    UpdateProjectRegistryQuotaAction,
    UpdateProjectRegistryQuotaActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def make_project_registry_quota_client(
    type_: ContainerRegistryType,
) -> AbstractPerProjectRegistryQuotaClient:
    match type_:
        case ContainerRegistryType.HARBOR2:
            return PerProjectHarborQuotaClient()
        case _:
            raise GenericBadRequest(
                f"{type_} does not support registry quota per project management."
            )


class ProjectRegistryQuotaService:
    """Service for managing per-project container registry quotas."""

    def __init__(
        self,
        repository: AbstractProjectRegistryQuotaRepository,
    ) -> None:
        self._repository = repository

    async def _get_client_and_context(
        self, scope_id: ProjectScope
    ) -> tuple[AbstractPerProjectRegistryQuotaClient, HarborProjectInfo, HarborAuthArgs]:
        registry_info = await self._repository.fetch_container_registry_row(scope_id)
        client = make_project_registry_quota_client(registry_info.type)
        project_info = HarborProjectInfo(
            url=registry_info.url,
            project=registry_info.project,
            ssl_verify=registry_info.ssl_verify,
        )
        credential = HarborAuthArgs(
            username=registry_info.username, password=registry_info.password
        )
        return client, project_info, credential

    async def create_quota(self, scope_id: ProjectScope, quota: int) -> None:
        client, project_info, credential = await self._get_client_and_context(scope_id)
        await client.create_quota(project_info, quota, credential)

    async def read_quota(self, scope_id: ProjectScope) -> int:
        client, project_info, credential = await self._get_client_and_context(scope_id)
        return await client.read_quota(project_info, credential)

    async def update_quota(self, scope_id: ProjectScope, quota: int) -> None:
        client, project_info, credential = await self._get_client_and_context(scope_id)
        await client.update_quota(project_info, quota, credential)

    async def delete_quota(self, scope_id: ProjectScope) -> None:
        client, project_info, credential = await self._get_client_and_context(scope_id)
        await client.delete_quota(project_info, credential)

    # Action-based methods for Processors pattern

    async def create_project_registry_quota(
        self, action: CreateProjectRegistryQuotaAction
    ) -> CreateProjectRegistryQuotaActionResult:
        scope_id = ProjectScope(project_id=action.project_id, domain_name=None)
        await self.create_quota(scope_id, action.quota)
        return CreateProjectRegistryQuotaActionResult(project_id=action.project_id)

    async def read_project_registry_quota(
        self, action: ReadProjectRegistryQuotaAction
    ) -> ReadProjectRegistryQuotaActionResult:
        scope_id = ProjectScope(project_id=action.project_id, domain_name=None)
        quota = await self.read_quota(scope_id)
        return ReadProjectRegistryQuotaActionResult(project_id=action.project_id, quota=quota)

    async def update_project_registry_quota(
        self, action: UpdateProjectRegistryQuotaAction
    ) -> UpdateProjectRegistryQuotaActionResult:
        scope_id = ProjectScope(project_id=action.project_id, domain_name=None)
        await self.update_quota(scope_id, action.quota)
        return UpdateProjectRegistryQuotaActionResult(project_id=action.project_id)

    async def delete_project_registry_quota(
        self, action: DeleteProjectRegistryQuotaAction
    ) -> DeleteProjectRegistryQuotaActionResult:
        scope_id = ProjectScope(project_id=action.project_id, domain_name=None)
        await self.delete_quota(scope_id)
        return DeleteProjectRegistryQuotaActionResult(project_id=action.project_id)
