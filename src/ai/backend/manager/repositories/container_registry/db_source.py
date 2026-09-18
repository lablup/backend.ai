"""Queries for resolving a project's configured image registry."""

import uuid

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.errors.repository import AmbiguousEntityKeyError
from ai.backend.manager.models.container_registry.searchers import (
    ContainerRegistryByNameAndProjectSearcher,
)
from ai.backend.manager.models.project.queriers import ProjectQuerier
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class ContainerRegistryDBSource:
    _ops_provider: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops_provider = ops_provider

    async def fetch_image_commit_registry(self, project_id: uuid.UUID) -> ContainerRegistryData:
        async with self._ops_provider.read_ops() as ops:
            project = await ops.query_data(ProjectQuerier(project_id=ProjectID(project_id)))
            if project is None or project.container_registry is None:
                raise ContainerRegistryNotFound(
                    f"Container registry info does not exist or is invalid in the project. (project: {project_id})"
                )
            target = project.container_registry
            result = await ops.search_in_global(
                ContainerRegistryByNameAndProjectSearcher(
                    pagination=OffsetPagination(limit=10),
                    registry_name=target.registry_name,
                    project_name=target.project_name,
                )
            )
            if not result.items:
                raise ContainerRegistryNotFound(
                    f"Container registry row not found. (registry: {target.registry_name}, project: {target.project_name})"
                )
            if len(result.items) > 1:
                raise AmbiguousEntityKeyError(
                    f"Multiple container registries match registry {target.registry_name}, project {target.project_name}"
                )
            return result.items[0]
