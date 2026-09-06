"""Delete specs for a container registry and the project relation it takes part in."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.relation import RelationPurger
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
    RelationPurger[ProjectID, ContainerRegistryID, AssociationContainerRegistriesGroupsRow]
):
    """Unlinks a project (the scope) from a registry (the target)."""

    @override
    def row_class(self) -> type[AssociationContainerRegistriesGroupsRow]:
        return AssociationContainerRegistriesGroupsRow

    @override
    def conditions(self, scope: ProjectID, target: ContainerRegistryID) -> Sequence[QueryCondition]:
        return (
            lambda: AssociationContainerRegistriesGroupsRow.registry_id == target,
            lambda: AssociationContainerRegistriesGroupsRow.group_id == scope,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
