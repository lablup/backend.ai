"""Container registry writes: what lets a project reach a registry.

A registry is reachable from the projects it is allowed in: each such project owns
and governs the registry, so project-scoped permissions carry onto the images the
registry owns. Only this domain has that relation, so the primitives sit here:
:class:`ContainerRegistryWriteOps` extends the general write ops, and a repository
handed the general ones never sees them.
"""

from __future__ import annotations

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class ContainerRegistryWriteOps(V2WriteOps):
    """The general v2 write ops plus the registry-project reach."""

    async def provision_registry(self, registry_id: ContainerRegistryID) -> None:
        """Put the registry into the RBAC graph if it is not there yet.

        Registries created before the virtual-entity rollout have no node, and every
        relation written against one resolves-or-fails.
        """
        await self._provision([registry_id])

    async def enroll_registry_in_project(
        self, registry_id: ContainerRegistryID, project_id: ProjectID
    ) -> None:
        """Let the project reach the registry and the entities it owns: the project
        owns and governs the registry. A reach past the entity itself, which the
        mutual-read relation (``create_relation``) does not give."""
        await self._provision([project_id])
        await self._created_in(registry_id, [project_id])

    async def withdraw_registry_from_project(
        self, registry_id: ContainerRegistryID, project_id: ProjectID
    ) -> None:
        """Reverse :meth:`enroll_registry_in_project`.

        Silent for a project or registry that never had a virtual entity.
        """
        await self._disown(registry_id, [project_id])
        await self._ungovern(registry_id, [project_id])
