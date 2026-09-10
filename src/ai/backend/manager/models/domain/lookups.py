"""Lookup implementations for the domain table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.lookup import BulkDataLookup, DataLookup


@dataclass
class DomainNameLookup(DataLookup[DomainRow, DomainID]):
    """Resolves a domain's name into the domain it names."""

    name: DomainName

    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def entity_type(self) -> EntityType:
        return DomainEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: DomainRow.name == self.name]

    @override
    def to_entity_id(self, row: DomainRow) -> DomainID:
        return row.id


@dataclass
class DomainNamesLookup(BulkDataLookup[DomainName, DomainID]):
    """Resolves several names into the domains they name."""

    @override
    def build_query(self, keys: Sequence[DomainName]) -> sa.sql.Select[Any]:
        return sa.select(DomainRow.name, DomainRow.id).where(DomainRow.name.in_(keys))

    @override
    def to_entity_id(self, value: UUID) -> DomainID:
        return DomainID(value)
