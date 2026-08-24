"""Delete specs for container registries and their project associations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.container_registry_group import ContainerRegistryGroupID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
    ContainerRegistryGroupData,
)
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.purger import EntityPurger, FieldBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ContainerRegistryPurger(EntityPurger[ContainerRegistryRow, ContainerRegistryData]):
    """Deletes one container registry with the RBAC graph it left."""

    registry_id: ContainerRegistryID

    @override
    def entity_id(self) -> ContainerRegistryID:
        return self.registry_id

    @override
    def row_class(self) -> type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ContainerRegistryRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()


@dataclass
class ContainerRegistryProjectPurger(
    FieldBatchPurger[
        ContainerRegistryID,
        AssociationContainerRegistriesGroupsRow,
        ContainerRegistryGroupData,
    ],
):
    """Removes the registry's association with one project."""

    project_id: ProjectID

    @override
    def build_subquery(
        self, owner_id: ContainerRegistryID
    ) -> sa.sql.Select[tuple[AssociationContainerRegistriesGroupsRow]]:
        return sa.select(AssociationContainerRegistriesGroupsRow).where(
            sa.and_(
                AssociationContainerRegistriesGroupsRow.registry_id == owner_id,
                AssociationContainerRegistriesGroupsRow.group_id == self.project_id,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AssociationContainerRegistriesGroupsRow) -> ContainerRegistryGroupData:
        return ContainerRegistryGroupData(
            id=ContainerRegistryGroupID(row.id),
            registry_id=ContainerRegistryID(row.registry_id),
            project_id=ProjectID(row.group_id),
        )


@dataclass
class ContainerRegistryProjectsPurger(
    FieldBatchPurger[
        ContainerRegistryID,
        AssociationContainerRegistriesGroupsRow,
        ContainerRegistryGroupData,
    ],
):
    """Removes every project association of the registry."""

    @override
    def build_subquery(
        self, owner_id: ContainerRegistryID
    ) -> sa.sql.Select[tuple[AssociationContainerRegistriesGroupsRow]]:
        return sa.select(AssociationContainerRegistriesGroupsRow).where(
            AssociationContainerRegistriesGroupsRow.registry_id == owner_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AssociationContainerRegistriesGroupsRow) -> ContainerRegistryGroupData:
        return ContainerRegistryGroupData(
            id=ContainerRegistryGroupID(row.id),
            registry_id=ContainerRegistryID(row.registry_id),
            project_id=ProjectID(row.group_id),
        )
