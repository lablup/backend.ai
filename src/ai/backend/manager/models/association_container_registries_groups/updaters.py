"""Update specs for a project's default container registry."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import (
    AssociationContainerRegistriesGroupsData,
)
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.association_container_registries_groups.searchable_fields import (
    AssociationContainerRegistriesGroupsSearchableFields,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater


@dataclass
class ClearDefaultRegistryUpdater(
    DataBatchUpdater[
        AssociationContainerRegistriesGroupsRow, AssociationContainerRegistriesGroupsData
    ]
):
    """Clear the project's default registry. The project's links are locked in id order
    first, so a concurrent switch waits for this one."""

    project_id: ProjectID

    @property
    @override
    def row_class(self) -> type[AssociationContainerRegistriesGroupsRow]:
        return AssociationContainerRegistriesGroupsRow

    @override
    def conditions(self) -> list[QueryCondition]:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            row = AssociationContainerRegistriesGroupsRow
            locked = (
                sa.select(row.id)
                .where(row.project_id == self.project_id)
                .order_by(row.id)
                .with_for_update()
            )
            return row.id.in_(locked)

        return [inner, lambda: AssociationContainerRegistriesGroupsRow.is_default.is_(True)]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": False}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(
        self, row: AssociationContainerRegistriesGroupsRow
    ) -> AssociationContainerRegistriesGroupsData:
        return AssociationContainerRegistriesGroupsSearchableFields.own.to_data(row)


@dataclass
class SetDefaultRegistryUpdater(
    DataBatchUpdater[
        AssociationContainerRegistriesGroupsRow, AssociationContainerRegistriesGroupsData
    ]
):
    """Make the project's link to the registry its default. The previous default must be
    cleared first: the partial unique index allows one per project."""

    registry_id: ContainerRegistryID

    @property
    @override
    def row_class(self) -> type[AssociationContainerRegistriesGroupsRow]:
        return AssociationContainerRegistriesGroupsRow

    @override
    def conditions(self) -> list[QueryCondition]:
        registry_id = self.registry_id
        return [lambda: AssociationContainerRegistriesGroupsRow.registry_id == registry_id]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": True}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(
        self, row: AssociationContainerRegistriesGroupsRow
    ) -> AssociationContainerRegistriesGroupsData:
        return AssociationContainerRegistriesGroupsSearchableFields.own.to_data(row)
