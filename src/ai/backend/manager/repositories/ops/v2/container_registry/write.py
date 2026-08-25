"""Container registry writes: the edges that let a project reach a registry.

A registry is reachable from the projects it is allowed in, and that reach is graph
edges rather than a row of its own — the registry joins each project's virtual scope
and each project is bound into the registry's, so project-scoped permissions carry
onto the images the registry owns. Only this domain has that relation, so the
primitives sit here: :class:`ContainerRegistryWriteOps` extends the general write ops,
and a repository handed the general ones never sees them.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class ContainerRegistryWriteOps(V2WriteOps):
    """The general v2 write ops plus the registry-project reach edges."""

    async def provision_registry(self, registry_id: ContainerRegistryID) -> None:
        """Put the registry into the RBAC graph if it is not there yet.

        Registries created before the virtual-scope rollout have no node, and every
        edge written against one resolves-or-fails.
        """
        await self._provision_entities([registry_id])

    async def enroll_registry_in_project(
        self, registry_id: ContainerRegistryID, project_id: ProjectID
    ) -> None:
        """Let the project reach the registry and the entities it owns."""
        await self._provision_entities([project_id])
        await self._enroll_member(registry_id, [project_id])

    async def withdraw_registry_from_project(
        self, registry_id: ContainerRegistryID, project_id: ProjectID
    ) -> None:
        """Reverse :meth:`enroll_registry_in_project`.

        Matches through the virtual scope nodes rather than resolving them first, so a
        project or registry that never had one is a no-op instead of a failure.
        """
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_scope_id.in_(
                    sa.select(VirtualScopeRow.id).where(
                        VirtualScopeRow.scope_type == project_id.entity_type(),
                        VirtualScopeRow.scope_id == project_id,
                    )
                ),
                EntityMembershipRow.entity_type == registry_id.entity_type(),
                EntityMembershipRow.entity_id == registry_id,
            )
        )
        await self._sess.execute(
            sa.delete(ScopeBindingRow).where(
                ScopeBindingRow.virtual_scope_id.in_(
                    sa.select(VirtualScopeRow.id).where(
                        VirtualScopeRow.scope_type == registry_id.entity_type(),
                        VirtualScopeRow.scope_id == registry_id,
                    )
                ),
                ScopeBindingRow.scope_type == project_id.entity_type(),
                ScopeBindingRow.scope_id == project_id,
            )
        )
