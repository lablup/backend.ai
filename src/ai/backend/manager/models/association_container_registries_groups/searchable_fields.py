from typing import override

from ai.backend.manager.data.container_registry.types import (
    AssociationContainerRegistriesGroupsData,
)
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _AssociationContainerRegistriesGroupsOwnFields(
    RowDataConverter[
        AssociationContainerRegistriesGroupsRow, AssociationContainerRegistriesGroupsData
    ]
):
    id = SearchableField(
        AssociationContainerRegistriesGroupsRow.id,
        UUIDConditions(AssociationContainerRegistriesGroupsRow.id),
        ColumnOrder(AssociationContainerRegistriesGroupsRow.id),
    )
    group_id = SearchableField(
        AssociationContainerRegistriesGroupsRow.group_id,
        UUIDConditions(AssociationContainerRegistriesGroupsRow.group_id),
        ColumnOrder(AssociationContainerRegistriesGroupsRow.group_id),
    )
    registry_id = SearchableField(
        AssociationContainerRegistriesGroupsRow.registry_id,
        UUIDConditions(AssociationContainerRegistriesGroupsRow.registry_id),
        ColumnOrder(AssociationContainerRegistriesGroupsRow.registry_id),
    )
    is_default = SearchableField(
        AssociationContainerRegistriesGroupsRow.is_default,
        BoolConditions(AssociationContainerRegistriesGroupsRow.is_default),
        ColumnOrder(AssociationContainerRegistriesGroupsRow.is_default),
    )

    @override
    def to_data(
        self, row: AssociationContainerRegistriesGroupsRow
    ) -> AssociationContainerRegistriesGroupsData:
        return AssociationContainerRegistriesGroupsData(
            id=self.id.read(row),
            group_id=self.group_id.read(row),
            registry_id=self.registry_id.read(row),
            is_default=self.is_default.read(row),
        )


class AssociationContainerRegistriesGroupsSearchableFields:
    own = _AssociationContainerRegistriesGroupsOwnFields()
