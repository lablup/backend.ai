"""Container registry reads: one by its id, and the lookups that name one."""

from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryID,
    ContainerRegistryName,
    ContainerRegistryProjectName,
)
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry.lookups import (
    ContainerRegistryByNameAndRegistryProjectLookup,
)
from ai.backend.manager.models.container_registry.queriers import ContainerRegistryQuerier
from ai.backend.manager.models.project.queriers import ProjectQuerier
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


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

    async def lookup_id_by_name_and_registry_project(
        self,
        registry_name: ContainerRegistryName,
        registry_project_name: ContainerRegistryProjectName | None,
    ) -> ContainerRegistryID:
        async with self._ops_provider.read_ops() as ops:
            registry_id = await ops.lookup_entity_id(
                ContainerRegistryByNameAndRegistryProjectLookup(
                    registry_name=registry_name, registry_project_name=registry_project_name
                )
            )
            if registry_id is None:
                raise ContainerRegistryNotFound(
                    f"Container registry row not found. (registry: {registry_name}, project: {registry_project_name})"
                )
            return registry_id

    async def lookup_image_commit_registry_id(self, project_id: ProjectID) -> ContainerRegistryID:
        async with self._ops_provider.read_ops() as ops:
            project = await ops.query_data(ProjectQuerier(project_id=project_id))
            if project is None or project.container_registry is None:
                raise ContainerRegistryNotFound(
                    f"Container registry info does not exist or is invalid in the project. (project: {project_id})"
                )
            target = project.container_registry
            registry_id = await ops.lookup_entity_id(
                ContainerRegistryByNameAndRegistryProjectLookup(
                    registry_name=ContainerRegistryName(target.registry_name),
                    registry_project_name=(
                        ContainerRegistryProjectName(target.project_name)
                        if target.project_name is not None
                        else None
                    ),
                )
            )
            if registry_id is None:
                raise ContainerRegistryNotFound(
                    f"Container registry row not found. (registry: {target.registry_name}, project: {target.project_name})"
                )
            return registry_id
