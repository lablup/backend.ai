from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.container_registry.types import (
    AssociationContainerRegistriesGroupsData,
)
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.association_container_registries_groups.searchable_fields import (
    AssociationContainerRegistriesGroupsSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class AssociationContainerRegistriesGroupsSearcher(
    Searcher[AssociationContainerRegistriesGroupsRow, AssociationContainerRegistriesGroupsData]
):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AssociationContainerRegistriesGroupsRow)

    @override
    def to_data(
        self, row: AssociationContainerRegistriesGroupsRow
    ) -> AssociationContainerRegistriesGroupsData:
        return AssociationContainerRegistriesGroupsSearchableFields.own.to_data(row)
