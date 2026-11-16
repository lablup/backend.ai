"""Lookup implementations for the links between projects and container registries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.specs.lookup import BulkDataLookup

__all__ = ("ProjectDefaultRegistriesLookup",)


@dataclass
class ProjectDefaultRegistriesLookup(BulkDataLookup[ProjectID, ContainerRegistryID]):
    """Resolves several projects into their default registries. A project without one is
    absent from the answer."""

    @override
    def build_query(self, keys: Sequence[ProjectID]) -> sa.sql.Select[Any]:
        return sa.select(
            AssociationContainerRegistriesGroupsRow.project_id,
            AssociationContainerRegistriesGroupsRow.registry_id,
        ).where(
            AssociationContainerRegistriesGroupsRow.project_id.in_(keys),
            AssociationContainerRegistriesGroupsRow.is_default,
        )

    @override
    def to_entity_id(self, value: UUID) -> ContainerRegistryID:
        return ContainerRegistryID(value)
