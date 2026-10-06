from collections.abc import Mapping

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.association_container_registries_groups.queriers import (
    DefaultContainerRegistryQuery,
)
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.container_registry.searchable_fields import (
    ContainerRegistrySearchableFields,
)
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps


class ProjectRegistryReadOps(V2ReadOps):
    async def default_registries(
        self, query: DefaultContainerRegistryQuery
    ) -> Mapping[ProjectID, ContainerRegistryData]:
        if not query.project_ids:
            return {}
        association = AssociationContainerRegistriesGroupsRow
        rows = await self._sess.execute(
            sa.select(association.group_id, ContainerRegistryRow)
            .join(ContainerRegistryRow, ContainerRegistryRow.id == association.registry_id)
            .where(association.group_id.in_(query.project_ids), association.is_default)
        )
        return {
            project_id: ContainerRegistrySearchableFields.own.to_data(registry)
            for project_id, registry in rows
        }
