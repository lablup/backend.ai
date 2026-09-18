"""Container registry reads: by id, by registry and project names, and by owning project."""

import uuid

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.errors.repository import AmbiguousEntityKeyError
from ai.backend.manager.models.container_registry.queriers import ContainerRegistryQuerier
from ai.backend.manager.models.container_registry.searchers import (
    ContainerRegistryByNameAndProjectSearcher,
)
from ai.backend.manager.models.project.queriers import ProjectQuerier
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps


class ContainerRegistryDBSource:
    _ops_provider: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops_provider = ops_provider

    async def fetch_by_id(self, registry_id: ContainerRegistryID) -> ContainerRegistryData:
        async with self._ops_provider.read_ops() as ops:
            registry = await ops.query_data(ContainerRegistryQuerier(registry_id=registry_id))
            if registry is None:
                raise ContainerRegistryNotFound(f"Container registry {registry_id} not found")
            return registry

    async def fetch_by_name_and_project(
        self, registry_name: str, project_name: str
    ) -> ContainerRegistryData:
        async with self._ops_provider.read_ops() as ops:
            return await self._search_one(ops, registry_name, project_name)

    async def fetch_image_commit_registry(self, project_id: uuid.UUID) -> ContainerRegistryData:
        async with self._ops_provider.read_ops() as ops:
            project = await ops.query_data(ProjectQuerier(project_id=ProjectID(project_id)))
            if project is None or project.container_registry is None:
                raise ContainerRegistryNotFound(
                    f"Container registry info does not exist or is invalid in the project. (project: {project_id})"
                )
            target = project.container_registry
            return await self._search_one(ops, target.registry_name, target.project_name)

    async def _search_one(
        self, ops: V2ReadOps, registry_name: str, project_name: str
    ) -> ContainerRegistryData:
        result = await ops.search_in_global(
            ContainerRegistryByNameAndProjectSearcher(
                pagination=OffsetPagination(limit=10),
                registry_name=registry_name,
                project_name=project_name,
            )
        )
        if not result.items:
            raise ContainerRegistryNotFound(
                f"Container registry row not found. (registry: {registry_name}, project: {project_name})"
            )
        if len(result.items) > 1:
            raise AmbiguousEntityKeyError(
                f"Multiple container registries match registry {registry_name}, project {project_name}"
            )
        return result.items[0]
