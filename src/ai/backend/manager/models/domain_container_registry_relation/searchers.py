from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.container_registry.types import DomainContainerRegistryRelationData
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.domain_container_registry_relation.searchable_fields import (
    DomainContainerRegistryRelationSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = ("DomainContainerRegistryRelationSearcher",)


@dataclass
class DomainContainerRegistryRelationSearcher(
    Searcher[DomainContainerRegistryRelationRow, DomainContainerRegistryRelationData]
):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DomainContainerRegistryRelationRow)

    @override
    def to_data(
        self, row: DomainContainerRegistryRelationRow
    ) -> DomainContainerRegistryRelationData:
        return DomainContainerRegistryRelationSearchableFields.own.to_data(row)
