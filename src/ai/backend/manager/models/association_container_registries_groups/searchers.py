from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.container_registry.types import (
    AssociationContainerRegistriesGroupsData,
)
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.association_container_registries_groups.searchable_fields import (
    AssociationContainerRegistriesGroupsSearchableFields,
)
from ai.backend.manager.models.rbac_models.permission.queries import entity_read_permission
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass(kw_only=True)
class AssociationContainerRegistriesGroupsSearcher(
    Searcher[AssociationContainerRegistriesGroupsRow, AssociationContainerRegistriesGroupsData]
):
    user_id: UserID

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AssociationContainerRegistriesGroupsRow).where(
            entity_read_permission(
                self.user_id, ProjectEntityType(), AssociationContainerRegistriesGroupsRow.group_id
            ),
            entity_read_permission(
                self.user_id,
                ContainerRegistryEntityType(),
                AssociationContainerRegistriesGroupsRow.registry_id,
            ),
        )

    @override
    def to_data(
        self, row: AssociationContainerRegistriesGroupsRow
    ) -> AssociationContainerRegistriesGroupsData:
        return AssociationContainerRegistriesGroupsSearchableFields.own.to_data(row)
